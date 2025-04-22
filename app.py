import networkx as nx
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, ttk

class ResourceAllocationGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_process(self, process):
        if process not in self.graph.nodes:
            self.graph.add_node(process, type="process")
            return True
        return False

    def add_resource(self, resource, instances=1):
        if resource not in self.graph.nodes:
            self.graph.add_node(resource, type="resource", instances=instances, allocated=0)
            return True
        return False

    def request_resource(self, process, resource):
        if self.graph.has_node(process) and self.graph.has_node(resource):
            if not self.graph.has_edge(process, resource):
                self.graph.add_edge(process, resource, type="request")

    def allocate_resource(self, process, resource):
        if self.graph.has_edge(process, resource):
            if self.graph.nodes[resource]['allocated'] < self.graph.nodes[resource]['instances']:
                self.graph.remove_edge(process, resource)
                self.graph.add_edge(resource, process, type="allocation")
                self.graph.nodes[resource]['allocated'] += 1
                return True
        return False

    def release_resource(self, process, resource):
        if self.graph.has_edge(resource, process):
            self.graph.remove_edge(resource, process)
            self.graph.nodes[resource]['allocated'] -= 1

    def detect_deadlock(self):
        try:
            # Step 1: Find any cycle
            cycle = nx.find_cycle(self.graph, orientation='original')
        
            # Step 2: Validate if the cycle is a real deadlock
            for i in range(len(cycle)):
                u, v, _ = cycle[i]

                # If it's a process requesting a resource
                if self.graph.nodes[u]['type'] == "process" and self.graph.nodes[v]['type'] == "resource":
                    resource = v
                    # Check if all instances of the resource are allocated
                    if self.graph.nodes[resource]['allocated'] < self.graph.nodes[resource]['instances']:
                        # Not a deadlock — process can eventually get it
                        return None

            # All resources in cycle are fully allocated => real deadlock
            return cycle

        except nx.NetworkXNoCycle:
            return None


    def visualize_graph(self):
        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(self.graph)
        node_colors = ["lightblue" if self.graph.nodes[n]["type"] == "process" else "lightgreen" for n in self.graph.nodes()]
        labels = {node: node for node in self.graph.nodes()}
        edges = nx.get_edge_attributes(self.graph, 'type')
        edge_colors = ['red' if edges[edge] == 'request' else 'green' for edge in self.graph.edges()]
        nx.draw(self.graph, pos, with_labels=True, node_color=node_colors, edge_color=edge_colors, node_size=2000)
        plt.show()

class ResourceGraphGUI:
    def __init__(self, root):
        self.graph = ResourceAllocationGraph()
        self.root = root
        self.root.title("Resource Allocation Graph Simulator")

        tk.Label(root, text="Process Name:").grid(row=0, column=0)
        self.process_entry = tk.Entry(root)
        self.process_entry.grid(row=0, column=1)

        tk.Label(root, text="Resource Name:").grid(row=1, column=0)
        self.resource_entry = tk.Entry(root)
        self.resource_entry.grid(row=1, column=1)

        tk.Label(root, text="Instance Count:").grid(row=2, column=0)
        self.instance_entry = tk.Entry(root)
        self.instance_entry.grid(row=2, column=1)

        tk.Button(root, text="Add Process", command=self.add_process).grid(row=3, column=0)
        tk.Button(root, text="Add Resource", command=self.add_resource).grid(row=3, column=1)
        tk.Button(root, text="Request Resource", command=self.request_resource).grid(row=4, column=0)
        tk.Button(root, text="Allocate Resource", command=self.allocate_resource).grid(row=4, column=1)
        tk.Button(root, text="Release Resource", command=self.release_resource).grid(row=5, column=0)
        tk.Button(root, text="Detect Deadlock", command=self.detect_deadlock).grid(row=5, column=1)
        tk.Button(root, text="Show Graph", command=self.show_graph).grid(row=6, column=0)
        tk.Button(root, text="Show Process Table", command=self.show_summary_table).grid(row=6, column=1)
        tk.Button(root, text="Reset", command=self.reset_graph).grid(row=7, column=0, columnspan=2, pady=5)

        self.check_deadlock_periodically()  # Start automatic deadlock detection

    def add_process(self):
        process = self.process_entry.get().strip()
        if process and self.graph.add_process(process):
            messagebox.showinfo("Success", f"Process {process} added.")
        else:
            messagebox.showwarning("Warning", f"Process {process} already exists!")

    def add_resource(self):
        resource = self.resource_entry.get().strip()
        instance_text = self.instance_entry.get().strip()

        # Default to 1 if left blank
        if instance_text == "":
            instances = 1
        elif instance_text.isdigit() and int(instance_text) > 0:
            instances = int(instance_text)
        else:
            messagebox.showerror("Error", "Please enter a valid positive number for instance count.")
            return

        if resource and self.graph.add_resource(resource, instances):
            messagebox.showinfo("Success", f"Resource {resource} with {instances} instance(s) added.")
        else:
            messagebox.showwarning("Warning", f"Resource {resource} already exists!")


    def request_resource(self):
        process = self.process_entry.get().strip()
        resource = self.resource_entry.get().strip()
        if process and resource:
            self.graph.request_resource(process, resource)
            messagebox.showinfo("Success", f"Process {process} requested Resource {resource}.")

    def allocate_resource(self):
        process = self.process_entry.get().strip()
        resource = self.resource_entry.get().strip()
        if process and resource:
            if self.graph.allocate_resource(process, resource):
                messagebox.showinfo("Success", f"Resource {resource} allocated to Process {process}.")
            else:
                messagebox.showerror("Error", f"Resource {resource} is fully allocated!")

    def release_resource(self):
        process = self.process_entry.get().strip()
        resource = self.resource_entry.get().strip()
        if process and resource:
            self.graph.release_resource(process, resource)
            messagebox.showinfo("Success", f"Resource {resource} released from Process {process}.")

    def show_graph(self):
        if len(self.graph.graph.nodes) == 0:
            messagebox.showinfo("Info", "Graph is empty! Add processes and resources first.")
        else:
            self.graph.visualize_graph()

    def check_deadlock_periodically(self):
        """Automatically checks for deadlocks and shows a popup if detected."""
        deadlock = self.graph.detect_deadlock()
        if deadlock:
            if not hasattr(self, 'deadlock_reported') or not self.deadlock_reported:
                messagebox.showerror("Deadlock Detected!", f"Deadlock found: {deadlock}")
                self.deadlock_reported = True
                self.explain_deadlock_reason(deadlock)
        else:
            self.deadlock_reported = False  # Reset flag when no deadlock is found
        self.root.after(5000, self.check_deadlock_periodically)

    def detect_deadlock(self):
        deadlock = self.graph.detect_deadlock()
        if deadlock:
            messagebox.showerror("Deadlock Detected!", f"Deadlock found: {deadlock}")
            self.explain_deadlock_reason(deadlock)  # Call the new feature here
        else:
            messagebox.showinfo("No Deadlock", "No deadlock detected.")

    def show_summary_table(self):
        """Opens a new window to display the resource allocation summary table."""
        summary_window = tk.Toplevel(self.root)
        summary_window.title("Resource Allocation Summary")
        summary_window.geometry("600x500")

        tree = ttk.Treeview(summary_window, columns=("Process", "Allocated Resources", "Requested Resources", "Status"), show="headings")
        tree.heading("Process", text="Process")
        tree.heading("Allocated Resources", text="Allocated Resources")
        tree.heading("Requested Resources", text="Requested Resources")
        tree.heading("Status", text="Process State")

        # Insert process details
        for node in self.graph.graph.nodes():
            if self.graph.graph.nodes[node]["type"] == "process":
                allocated_resources = [edge[0] for edge in self.graph.graph.in_edges(node) if self.graph.graph.nodes[edge[0]]["type"] == "resource"]
                requested_resources = [edge[1] for edge in self.graph.graph.out_edges(node) if self.graph.graph.nodes[edge[1]]["type"] == "resource"]
                
                # Updated process state logic
                if requested_resources:
                    status = "Waiting"
                else:
                    status = "Running"

                tree.insert("", "end", values=(node, ", ".join(allocated_resources) if allocated_resources else "None",
                                               ", ".join(requested_resources) if requested_resources else "None", status))

        tree.pack(fill=tk.BOTH, expand=True)

        # Resource status table
        resource_label = tk.Label(summary_window, text="Resource Status", font=("Arial", 12, "bold"))
        resource_label.pack()

        resource_tree = ttk.Treeview(summary_window, columns=("Resource", "Allocated/Total", "Status"), show="headings")
        resource_tree.heading("Resource", text="Resource")
        resource_tree.heading("Allocated/Total", text="Allocated/Total")
        resource_tree.heading("Status", text="Resource State")

        for node in self.graph.graph.nodes():
            if self.graph.graph.nodes[node]["type"] == "resource":
                allocated = self.graph.graph.nodes[node]["allocated"]
                instances = self.graph.graph.nodes[node]["instances"]
                status = "Allocated" if allocated > 0 else "Free"
                resource_tree.insert("", "end", values=(node, f"{allocated}/{instances}", status))

        resource_tree.pack(fill=tk.BOTH, expand=True)

    def explain_deadlock_reason(self, cycle):
        explanation = "🔍 Deadlock Explanation:\n\n"
        suggestion = "🛠 Suggested Action:\n\n"

        for i in range(len(cycle)):
            u, v, _ = cycle[i]
            u_type = self.graph.graph.nodes[u]['type']
            v_type = self.graph.graph.nodes[v]['type']

            if u_type == "process" and v_type == "resource":
                explanation += f"• {u} is waiting for {v}\n"
            elif u_type == "resource" and v_type == "process":
                explanation += f"• {u} is held by {v}\n"

        # Suggest releasing or reallocating resources
        suggestion += "Consider releasing one of the following resource allocations:\n"
        for i in range(len(cycle)):
            u, v, _ = cycle[i]
            if self.graph.graph.nodes[u]['type'] == "resource" and self.graph.graph.nodes[v]['type'] == "process":
                suggestion += f"→ Release {u} from {v}\n"

        messagebox.showerror("Deadlock Details", explanation + "\n" + suggestion)
        
    def reset_graph(self):
        confirm = messagebox.askyesno("Reset Confirmation", "Are you sure you want to reset everything?")
        if confirm:
            self.graph = ResourceAllocationGraph()
            self.process_entry.delete(0, tk.END)
            self.resource_entry.delete(0, tk.END)
            self.instance_entry.delete(0, tk.END)
            self.deadlock_reported = False
            messagebox.showinfo("Reset Done", "The simulator has been reset.")


if __name__ == "__main__":
    root = tk.Tk()
    app = ResourceGraphGUI(root)
    root.mainloop()
