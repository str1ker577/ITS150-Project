# CPU Process Simulation using Python
# ITS150 / AM4
# By John Christian Adao and Kyle Hendrik L. Lim

import tkinter as tk
from tkinter import ttk, messagebox
import random

class Process:
    """Process Control Block (PCB)"""
    def __init__(self, pid, arrival_time, burst_time, priority=0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority
        self.remaining_time = burst_time 
        self.completion_time = 0
        self.turnaround_time = 0
        self.waiting_time = 0
        self.remaining_time = burst_time

class CPUScheduler:
    def __init__(self, root):
        self.root = root
        self.root.title("⚙️ CPU Scheduling Simulator")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        
        self.processes = []
        self.setup_gui()
        
    def setup_gui(self):
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="⚙️ CPU SCHEDULING SIMULATOR", 
                font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white').pack(pady=15)
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left Panel - Input
        left_frame = ttk.LabelFrame(main_frame, text="📋 Process Input", padding=15)
        left_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        # Number of processes
        tk.Label(left_frame, text="Number of Processes (1-10):", font=('Arial', 10)).grid(row=0, column=0, sticky='w', pady=5)
        self.num_processes = tk.StringVar(value="5")
        tk.Entry(left_frame, textvariable=self.num_processes, width=10, font=('Arial', 10)).grid(row=0, column=1, pady=5)
        
        tk.Button(left_frame, text="Generate Random Processes", command=self.generate_random, 
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'), cursor='hand2').grid(row=1, column=0, columnspan=2, pady=10, sticky='ew')
        
        # Process entry table
        tk.Label(left_frame, text="Or Enter Manually:", font=('Arial', 10, 'bold')).grid(row=2, column=0, columnspan=2, pady=(10,5), sticky='w')
        
        table_frame = tk.Frame(left_frame)
        table_frame.grid(row=3, column=0, columnspan=2, pady=5)
        
        headers = ["P#", "Arrival", "Burst", "Priority"]
        for col, header in enumerate(headers):
            tk.Label(table_frame, text=header, font=('Arial', 9, 'bold'), width=8).grid(row=0, column=col, padx=2)
        
        self.entry_widgets = []
        for i in range(10):
            row_entries = []
            tk.Label(table_frame, text=f"P{i+1}", font=('Arial', 9), width=8).grid(row=i+1, column=0, padx=2, pady=2)
            for col in range(1, 4):
                entry = tk.Entry(table_frame, width=8, font=('Arial', 9))
                entry.grid(row=i+1, column=col, padx=2, pady=2)
                row_entries.append(entry)
            self.entry_widgets.append(row_entries)
        
        tk.Button(left_frame, text="Use Manual Input", command=self.use_manual_input,
                 bg='#2ecc71', fg='white', font=('Arial', 10, 'bold'), cursor='hand2').grid(row=4, column=0, columnspan=2, pady=10, sticky='ew')
        
        # Right Panel - Algorithm Selection
        right_frame = ttk.LabelFrame(main_frame, text="🔧 Algorithm Selection", padding=15)
        right_frame.grid(row=0, column=1, sticky='nsew')
        
        self.algorithm = tk.StringVar(value="fcfs")
        
        algorithms = [
            ("First Come First Serve (FCFS)", "fcfs"),
            ("Shortest Job First (SJF)", "sjf"),
            ("Round Robin (RR)", "rr"),
            ("Priority Scheduling", "priority")
        ]
        
        for i, (text, value) in enumerate(algorithms):
            tk.Radiobutton(right_frame, text=text, variable=self.algorithm, value=value,
                          font=('Arial', 11), bg='white', cursor='hand2').grid(row=i, column=0, sticky='w', pady=5, padx=5)
        
        # Time Quantum for RR
        tk.Label(right_frame, text="Time Quantum (for RR):", font=('Arial', 10)).grid(row=4, column=0, sticky='w', pady=(15,5))
        self.quantum = tk.StringVar(value="3")
        tk.Entry(right_frame, textvariable=self.quantum, width=10, font=('Arial', 10)).grid(row=5, column=0, sticky='w', pady=5)
        
        # Run Button
        tk.Button(right_frame, text="▶ RUN SIMULATION", command=self.run_simulation,
                 bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'), cursor='hand2', height=2).grid(row=6, column=0, pady=20, sticky='ew')
        
        # Results area
        results_frame = ttk.LabelFrame(main_frame, text="📊 Simulation Results", padding=15)
        results_frame.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=(20, 0))
        
        # Results text with scrollbar
        text_frame = tk.Frame(results_frame)
        text_frame.pack(fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.results_text = tk.Text(text_frame, height=15, font=('Courier', 9), 
                                    yscrollcommand=scrollbar.set, bg='#ecf0f1')
        self.results_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.results_text.yview)
        
        # Configure grid weights
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
    def generate_random(self):
        try:
            n = int(self.num_processes.get())
            if n < 1 or n > 10:
                messagebox.showerror("Error", "Number of processes must be between 1 and 10")
                return
                
            # Clear previous entries
            for row in self.entry_widgets:
                for entry in row:
                    entry.delete(0, tk.END)
            
            # Generate random values
            for i in range(n):
                arrival = random.randint(0, 10)
                burst = random.randint(1, 10)
                priority = random.randint(1, 5)
                
                self.entry_widgets[i][0].insert(0, str(arrival))
                self.entry_widgets[i][1].insert(0, str(burst))
                self.entry_widgets[i][2].insert(0, str(priority))
                
            messagebox.showinfo("Success", f"Generated {n} random processes!")
            
        except ValueError:
            messagebox.showerror("Error", "Invalid number of processes")
    
    def use_manual_input(self):
        messagebox.showinfo("Manual Input", "Fill in the table above and click RUN SIMULATION")
    
    def read_processes(self):
        self.processes = []
        try:
            n = int(self.num_processes.get())
            if n < 1 or n > 10:
                messagebox.showerror("Error", "Number of processes must be between 1 and 10")
                return False
            
            for i in range(n):
                arrival = self.entry_widgets[i][0].get()
                burst = self.entry_widgets[i][1].get()
                priority = self.entry_widgets[i][2].get()
                
                if not arrival or not burst:
                    messagebox.showerror("Error", f"Please fill Arrival and Burst time for P{i+1}")
                    return False
                
                arrival = int(arrival)
                burst = int(burst)
                priority = int(priority) if priority else 0
                
                if burst <= 0:
                    messagebox.showerror("Error", f"Burst time for P{i+1} must be positive")
                    return False
                
                self.processes.append(Process(i+1, arrival, burst, priority))
            
            return True
            
        except ValueError:
            messagebox.showerror("Error", "Invalid input. Please enter valid numbers.")
            return False
    
    def run_simulation(self):
        if not self.read_processes():
            return
        
        algo = self.algorithm.get()
        
        if algo == "fcfs":
            self.fcfs()
        elif algo == "sjf":
            self.sjf()
        elif algo == "rr":
            try:
                quantum = int(self.quantum.get())
                if quantum <= 0:
                    messagebox.showerror("Error", "Time quantum must be positive")
                    return
                self.round_robin(quantum)
            except ValueError:
                messagebox.showerror("Error", "Invalid time quantum")
        elif algo == "priority":
            self.priority_scheduling()
    
    def fcfs(self):
        """First Come First Serve"""
        processes = sorted(self.processes, key=lambda p: p.arrival_time)
        current_time = 0
        gantt = []
        
        for p in processes:
            if current_time < p.arrival_time:
                current_time = p.arrival_time
            
            gantt.append(f"P{p.pid}")
            current_time += p.burst_time
            p.completion_time = current_time
            p.turnaround_time = p.completion_time - p.arrival_time
            p.waiting_time = p.turnaround_time - p.burst_time
        
        self.display_results("First Come First Serve (FCFS)", processes, gantt)
    
    def sjf(self):
        """Shortest Job First - Non-preemptive"""
        processes = self.processes.copy()
        n = len(processes)
        current_time = 0
        completed = []
        gantt = []
        
        while len(completed) < n:
            # Find available processes
            available = [p for p in processes if p.arrival_time <= current_time and p not in completed]
            
            if not available:
                current_time += 1
                continue
            
            # Select shortest job
            shortest = min(available, key=lambda p: p.burst_time)
            gantt.append(f"P{shortest.pid}")
            current_time += shortest.burst_time
            shortest.completion_time = current_time
            shortest.turnaround_time = shortest.completion_time - shortest.arrival_time
            shortest.waiting_time = shortest.turnaround_time - shortest.burst_time
            completed.append(shortest)
        
        self.display_results("Shortest Job First (SJF)", processes, gantt)
    
    def round_robin(self, quantum):
        """Round Robin"""
        processes = [Process(p.pid, p.arrival_time, p.burst_time, p.priority) for p in self.processes]
        current_time = 0
        queue = []
        gantt = []
        completed = []
        
        # Sort by arrival time
        processes.sort(key=lambda p: p.arrival_time)
        idx = 0
        
        # Add first process(es)
        while idx < len(processes) and processes[idx].arrival_time <= current_time:
            queue.append(processes[idx])
            idx += 1
        
        while queue or idx < len(processes):
            if not queue:
                current_time = processes[idx].arrival_time
                queue.append(processes[idx])
                idx += 1
            
            current = queue.pop(0)
            gantt.append(f"P{current.pid}")
            
            exec_time = min(quantum, current.remaining_time)
            current_time += exec_time
            current.remaining_time -= exec_time
            
            # Add newly arrived processes
            while idx < len(processes) and processes[idx].arrival_time <= current_time:
                queue.append(processes[idx])
                idx += 1
            
            if current.remaining_time > 0:
                queue.append(current)
            else:
                current.completion_time = current_time
                current.turnaround_time = current.completion_time - current.arrival_time
                current.waiting_time = current.turnaround_time - current.burst_time
                completed.append(current)
        
        # FIX: Pass 'processes' instead of 'self.processes'
        self.display_results(f"Round Robin (Time Quantum = {quantum})", processes, gantt)
    
    def priority_scheduling(self):
        """Priority Scheduling - Non-preemptive (Lower number = Higher priority)"""
        processes = self.processes.copy()
        n = len(processes)
        current_time = 0
        completed = []
        gantt = []
        
        while len(completed) < n:
            # Find available processes
            available = [p for p in processes if p.arrival_time <= current_time and p not in completed]
            
            if not available:
                current_time += 1
                continue
            
            # Select highest priority (lowest number)
            highest_priority = min(available, key=lambda p: p.priority)
            gantt.append(f"P{highest_priority.pid}")
            current_time += highest_priority.burst_time
            highest_priority.completion_time = current_time
            highest_priority.turnaround_time = highest_priority.completion_time - highest_priority.arrival_time
            highest_priority.waiting_time = highest_priority.turnaround_time - highest_priority.burst_time
            completed.append(highest_priority)
        
        self.display_results("Priority Scheduling (Non-preemptive)", processes, gantt)
    
    def display_results(self, algorithm_name, processes, gantt):
        self.results_text.delete(1.0, tk.END)
        
        # Header
        result = f"\n{'='*80}\n"
        result += f"  RESULTS FOR: {algorithm_name}\n"
        result += f"{'='*80}\n\n"
        
        # Process table
        result += f"{'Process':<10} {'Arrival':<10} {'Burst':<10} {'Complete':<10} {'TAT':<10} {'Waiting':<10}\n"
        result += f"{'-'*70}\n"
        
        for p in sorted(processes, key=lambda x: x.pid):
            result += f"{'P'+str(p.pid):<10} {p.arrival_time:<10} {p.burst_time:<10} "
            result += f"{p.completion_time:<10} {p.turnaround_time:<10} {p.waiting_time:<10}\n"
        
        # Averages
        avg_tat = sum(p.turnaround_time for p in processes) / len(processes)
        avg_wt = sum(p.waiting_time for p in processes) / len(processes)
        
        result += f"\n{'-'*70}\n"
        result += f"Average Turnaround Time = {avg_tat:.2f}\n"
        result += f"Average Waiting Time    = {avg_wt:.2f}\n"
        
        # Gantt Chart
        result += f"\n{'='*80}\n"
        result += f"  GANTT CHART (Execution Timeline)\n"
        result += f"{'='*80}\n\n"
        result += "  " + " → ".join(gantt) + "\n"
        
        self.results_text.insert(1.0, result)

if __name__ == "__main__":
    root = tk.Tk()
    app = CPUScheduler(root)
    root.mainloop()