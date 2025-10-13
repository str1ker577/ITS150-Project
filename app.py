import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import numpy as np
import random
import threading
import time
from collections import deque
import statistics

class Process:
    """Process Control Block (PCB) - represents a process in the system"""
    def __init__(self, arrival_time, process_id):
        self.process_id = process_id
        self.arrival_time = arrival_time
        self.burst_time = None  # Total CPU time needed
        self.remaining_time = None  # For preemptive algorithms
        self.priority = None  # For priority scheduling
        self.start_time = None  # When process first gets CPU
        self.completion_time = None  # When process finishes
        self.waiting_time = 0  # Time spent in ready queue
        self.turnaround_time = 0  # Total time from arrival to completion
        self.response_time = None  # Time from arrival to first execution
        self.state = "NEW"  # NEW, READY, RUNNING, TERMINATED

class ProcessSchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚙️ Process Scheduling Simulator")
        self.root.geometry("1200x900")
        self.root.configure(bg='#f0f0f0')
        
        # Simulation parameters
        self.simulation_running = False
        self.simulation_thread = None
        self.current_time = 0
        self.processes = []
        self.completed_processes = []
        
        # Animation data
        self.time_points = []
        self.ready_queue_data = []
        self.gantt_data = []  # For Gantt chart: [(start_time, process_id, duration)]
        
        self.setup_gui()
        
    def setup_gui(self):
        # Create main frames
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        viz_frame = ttk.Frame(self.root)
        viz_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Control Panel
        ttk.Label(control_frame, text="⚙️ Process Scheduling Simulator", 
                 font=('Arial', 16, 'bold')).grid(row=0, column=0, columnspan=4, pady=10)
        
        # Input parameters
        params_frame = ttk.LabelFrame(control_frame, text="Simulation Parameters", padding=10)
        params_frame.grid(row=1, column=0, columnspan=4, sticky='ew', pady=5)
        
        # Number of processes
        ttk.Label(params_frame, text="Number of Processes:").grid(row=0, column=0, sticky='w')
        self.num_processes_var = tk.StringVar(value="10")
        ttk.Entry(params_frame, textvariable=self.num_processes_var, width=10).grid(row=0, column=1, padx=5)
        
        # Arrival time range
        ttk.Label(params_frame, text="Arrival Time (ms):").grid(row=0, column=2, sticky='w', padx=(20,0))
        self.arrival_min_var = tk.StringVar(value="0")
        self.arrival_max_var = tk.StringVar(value="50")
        ttk.Entry(params_frame, textvariable=self.arrival_min_var, width=5).grid(row=0, column=3, padx=2)
        ttk.Label(params_frame, text="to").grid(row=0, column=4)
        ttk.Entry(params_frame, textvariable=self.arrival_max_var, width=5).grid(row=0, column=5, padx=2)
        
        # Burst time range
        ttk.Label(params_frame, text="Burst Time (ms):").grid(row=1, column=0, sticky='w')
        self.burst_min_var = tk.StringVar(value="5")
        self.burst_max_var = tk.StringVar(value="25")
        ttk.Entry(params_frame, textvariable=self.burst_min_var, width=5).grid(row=1, column=1, padx=2)
        ttk.Label(params_frame, text="to").grid(row=1, column=2)
        ttk.Entry(params_frame, textvariable=self.burst_max_var, width=5).grid(row=1, column=3, padx=2)
        
        # Priority range (for priority scheduling)
        ttk.Label(params_frame, text="Priority Range:").grid(row=1, column=4, sticky='w', padx=(20,0))
        self.priority_min_var = tk.StringVar(value="1")
        self.priority_max_var = tk.StringVar(value="5")
        ttk.Entry(params_frame, textvariable=self.priority_min_var, width=5).grid(row=1, column=5, padx=2)
        ttk.Label(params_frame, text="to").grid(row=1, column=6)
        ttk.Entry(params_frame, textvariable=self.priority_max_var, width=5).grid(row=1, column=7, padx=2)
        
        # Time Quantum (for Round Robin)
        ttk.Label(params_frame, text="Time Quantum (RR):").grid(row=2, column=0, sticky='w')
        self.quantum_var = tk.StringVar(value="5")
        ttk.Entry(params_frame, textvariable=self.quantum_var, width=10).grid(row=2, column=1, padx=5)
        ttk.Label(params_frame, text="ms").grid(row=2, column=2, sticky='w')
        
        # Algorithm selection
        algo_frame = ttk.LabelFrame(control_frame, text="Scheduling Algorithm", padding=10)
        algo_frame.grid(row=2, column=0, columnspan=4, sticky='ew', pady=5)
        
        self.algorithm_var = tk.StringVar(value="fcfs")
        algorithms = [
            ("FCFS (First Come First Serve)", "fcfs"),
            ("SJF (Shortest Job First)", "sjf"),
            ("SRTF (Shortest Remaining Time First)", "srtf"),
            ("Round Robin", "rr"),
            ("Priority Scheduling (Non-Preemptive)", "priority"),
            ("Priority Scheduling (Preemptive)", "priority_preemptive")
        ]
        
        for i, (text, value) in enumerate(algorithms):
            row = i // 3
            col = i % 3
            ttk.Radiobutton(algo_frame, text=text, variable=self.algorithm_var, 
                          value=value).grid(row=row, column=col, padx=10, pady=2, sticky='w')
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="▶️ Start Simulation", 
                                    command=self.start_simulation)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹️ Stop", 
                                   command=self.stop_simulation, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.reset_btn = ttk.Button(button_frame, text="🔄 Reset", 
                                    command=self.reset_simulation)
        self.reset_btn.grid(row=0, column=2, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Ready to simulate")
        ttk.Label(control_frame, textvariable=self.status_var, 
                 font=('Arial', 10)).grid(row=4, column=0, columnspan=4, pady=5)
        
        # Create visualization area
        self.setup_visualizations(viz_frame)
        
    def setup_visualizations(self, parent):
        # Create notebook for different views
        notebook = ttk.Notebook(parent)
        notebook.pack(fill='both', expand=True)
        
        # Real-time simulation tab
        sim_frame = ttk.Frame(notebook)
        notebook.add(sim_frame, text="🎬 Live Simulation")
        
        # Gantt chart tab
        gantt_frame = ttk.Frame(notebook)
        notebook.add(gantt_frame, text="📊 Gantt Chart")
        
        # Results tab
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="📈 Results")
        
        # Setup live simulation visualization
        self.fig_live, (self.ax_ready_queue, self.ax_timeline) = plt.subplots(2, 1, figsize=(10, 6))
        self.fig_live.suptitle('Live Process Scheduling Simulation', fontsize=14, fontweight='bold')
        plt.subplots_adjust(hspace=0.4)
        
        self.canvas_live = FigureCanvasTkAgg(self.fig_live, sim_frame)
        self.canvas_live.get_tk_widget().pack(fill='both', expand=True)
        
        # Setup ready queue plot
        self.ax_ready_queue.set_title('Ready Queue Length Over Time')
        self.ax_ready_queue.set_xlabel('Time (ms)')
        self.ax_ready_queue.set_ylabel('Processes in Ready Queue')
        self.ax_ready_queue.grid(True, alpha=0.3)
        
        # Setup timeline plot
        self.ax_timeline.set_title('Process Execution Timeline')
        self.ax_timeline.set_xlabel('Time (ms)')
        self.ax_timeline.set_ylabel('Cumulative Processes Completed')
        self.ax_timeline.grid(True, alpha=0.3)
        
        # Setup Gantt chart
        self.fig_gantt, self.ax_gantt = plt.subplots(figsize=(10, 6))
        self.fig_gantt.suptitle('Process Execution Gantt Chart', fontsize=14, fontweight='bold')
        
        self.canvas_gantt = FigureCanvasTkAgg(self.fig_gantt, gantt_frame)
        self.canvas_gantt.get_tk_widget().pack(fill='both', expand=True)
        
        # Setup results visualization
        self.fig_results, ((self.ax_throughput, self.ax_waiting), 
                          (self.ax_turnaround, self.ax_response)) = plt.subplots(2, 2, figsize=(10, 6))
        self.fig_results.suptitle('Scheduling Performance Analysis', fontsize=14, fontweight='bold')
        plt.subplots_adjust(hspace=0.4, wspace=0.3)
        
        self.canvas_results = FigureCanvasTkAgg(self.fig_results, results_frame)
        self.canvas_results.get_tk_widget().pack(fill='both', expand=True)
        
        # Results text area
        self.results_text = tk.Text(results_frame, height=10, font=('Courier', 9))
        self.results_text.pack(fill='x', padx=10, pady=5)
        
    def start_simulation(self):
        try:
            # Validate inputs
            num_processes = int(self.num_processes_var.get())
            arrival_min = int(self.arrival_min_var.get())
            arrival_max = int(self.arrival_max_var.get())
            burst_min = int(self.burst_min_var.get())
            burst_max = int(self.burst_max_var.get())
            priority_min = int(self.priority_min_var.get())
            priority_max = int(self.priority_max_var.get())
            quantum = int(self.quantum_var.get())
            
            if arrival_min > arrival_max or burst_min > burst_max or priority_min > priority_max:
                messagebox.showerror("Error", "Min values must be ≤ max values")
                return
                
            if num_processes < 1 or num_processes > 100:
                messagebox.showerror("Error", "Number of processes must be between 1 and 100")
                return
                
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return
        
        # Reset data
        self.reset_data()
        
        # Update UI
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.simulation_running = True
        
        # Start simulation in separate thread
        self.simulation_thread = threading.Thread(
            target=self.run_simulation,
            args=(num_processes, arrival_min, arrival_max, burst_min, burst_max, 
                  priority_min, priority_max, quantum)
        )
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
        # Start animation
        self.animation = FuncAnimation(self.fig_live, self.update_plots, interval=100, blit=False)
        
    def stop_simulation(self):
        self.simulation_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Simulation stopped")
        
        if hasattr(self, 'animation'):
            self.animation.event_source.stop()
            
    def reset_simulation(self):
        self.stop_simulation()
        self.reset_data()
        self.clear_plots()
        self.status_var.set("Ready to simulate")
        
    def reset_data(self):
        self.current_time = 0
        self.processes = []
        self.completed_processes = []
        self.time_points = []
        self.ready_queue_data = []
        self.gantt_data = []
        
    def clear_plots(self):
        for ax in [self.ax_ready_queue, self.ax_timeline, self.ax_gantt]:
            ax.clear()
        
        self.ax_ready_queue.set_title('Ready Queue Length Over Time')
        self.ax_ready_queue.set_xlabel('Time (ms)')
        self.ax_ready_queue.set_ylabel('Processes in Ready Queue')
        self.ax_ready_queue.grid(True, alpha=0.3)
        
        self.ax_timeline.set_title('Process Execution Timeline')
        self.ax_timeline.set_xlabel('Time (ms)')
        self.ax_timeline.set_ylabel('Cumulative Processes Completed')
        self.ax_timeline.grid(True, alpha=0.3)
        
        self.canvas_live.draw()
        self.canvas_gantt.draw()
        
    def generate_processes(self, num_processes, arrival_min, arrival_max, 
                          burst_min, burst_max, priority_min, priority_max):
        """Generate random processes with PCB attributes"""
        processes = []
        
        for i in range(1, num_processes + 1):
            arrival_time = random.randint(arrival_min, arrival_max)
            burst_time = random.randint(burst_min, burst_max)
            priority = random.randint(priority_min, priority_max)
            
            process = Process(arrival_time, i)
            process.burst_time = burst_time
            process.remaining_time = burst_time
            process.priority = priority
            
            processes.append(process)
        
        # Sort by arrival time
        processes.sort(key=lambda p: p.arrival_time)
        return processes
        
    def run_simulation(self, num_processes, arrival_min, arrival_max, 
                      burst_min, burst_max, priority_min, priority_max, quantum):
        # Generate processes
        self.processes = self.generate_processes(num_processes, arrival_min, arrival_max, 
                                                 burst_min, burst_max, priority_min, priority_max)
        
        # Run selected algorithm
        algorithm = self.algorithm_var.get()
        
        if algorithm == "fcfs":
            self.simulate_fcfs()
        elif algorithm == "sjf":
            self.simulate_sjf()
        elif algorithm == "srtf":
            self.simulate_srtf()
        elif algorithm == "rr":
            self.simulate_round_robin(quantum)
        elif algorithm == "priority":
            self.simulate_priority(preemptive=False)
        elif algorithm == "priority_preemptive":
            self.simulate_priority(preemptive=True)
            
        # Generate final results
        self.root.after(0, self.show_results)
        
    def simulate_fcfs(self):
        """First Come First Serve - Non-preemptive"""
        ready_queue = deque()
        current_time = 0
        process_index = 0
        
        while len(self.completed_processes) < len(self.processes):
            if not self.simulation_running:
                break
            
            # Add newly arrived processes to ready queue
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            # Execute process if available
            if ready_queue:
                process = ready_queue.popleft()
                process.state = "RUNNING"
                
                if process.start_time is None:
                    process.start_time = current_time
                    process.response_time = current_time - process.arrival_time
                
                # Record Gantt chart data
                self.gantt_data.append((current_time, process.process_id, process.burst_time))
                
                # Execute for full burst time (non-preemptive)
                current_time += process.burst_time
                
                # Process completed
                process.state = "TERMINATED"
                process.completion_time = current_time
                process.turnaround_time = current_time - process.arrival_time
                process.waiting_time = process.turnaround_time - process.burst_time
                
                self.completed_processes.append(process)
                
                self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
            else:
                # CPU idle
                current_time += 1
            
            time.sleep(0.01)  # Visualization delay
    
    def simulate_sjf(self):
        """Shortest Job First - Non-preemptive"""
        ready_queue = []
        current_time = 0
        process_index = 0
        
        while len(self.completed_processes) < len(self.processes):
            if not self.simulation_running:
                break
            
            # Add newly arrived processes
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            if ready_queue:
                # Sort by burst time (shortest first)
                ready_queue.sort(key=lambda p: p.burst_time)
                process = ready_queue.pop(0)
                process.state = "RUNNING"
                
                if process.start_time is None:
                    process.start_time = current_time
                    process.response_time = current_time - process.arrival_time
                
                self.gantt_data.append((current_time, process.process_id, process.burst_time))
                current_time += process.burst_time
                
                process.state = "TERMINATED"
                process.completion_time = current_time
                process.turnaround_time = current_time - process.arrival_time
                process.waiting_time = process.turnaround_time - process.burst_time
                
                self.completed_processes.append(process)
                self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
            else:
                current_time += 1
            
            time.sleep(0.01)
    
    def simulate_srtf(self):
        """Shortest Remaining Time First - Preemptive"""
        ready_queue = []
        current_time = 0
        process_index = 0
        current_process = None
        
        while len(self.completed_processes) < len(self.processes) or current_process:
            if not self.simulation_running:
                break
            
            # Add newly arrived processes
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            # If current process exists, add it back to queue for comparison
            if current_process:
                ready_queue.append(current_process)
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            if ready_queue:
                # Sort by remaining time
                ready_queue.sort(key=lambda p: p.remaining_time)
                process = ready_queue.pop(0)
                
                if process.start_time is None:
                    process.start_time = current_time
                    process.response_time = current_time - process.arrival_time
                
                process.state = "RUNNING"
                
                # Execute for 1 time unit
                self.gantt_data.append((current_time, process.process_id, 1))
                process.remaining_time -= 1
                current_time += 1
                
                if process.remaining_time == 0:
                    process.state = "TERMINATED"
                    process.completion_time = current_time
                    process.turnaround_time = current_time - process.arrival_time
                    process.waiting_time = process.turnaround_time - process.burst_time
                    self.completed_processes.append(process)
                    current_process = None
                    self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
                else:
                    current_process = process
            else:
                current_time += 1
                current_process = None
            
            time.sleep(0.005)
    
    def simulate_round_robin(self, quantum):
        """Round Robin - Preemptive with time quantum"""
        ready_queue = deque()
        current_time = 0
        process_index = 0
        
        while len(self.completed_processes) < len(self.processes):
            if not self.simulation_running:
                break
            
            # Add newly arrived processes
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            if ready_queue:
                process = ready_queue.popleft()
                
                if process.start_time is None:
                    process.start_time = current_time
                    process.response_time = current_time - process.arrival_time
                
                process.state = "RUNNING"
                
                # Execute for quantum or remaining time, whichever is smaller
                exec_time = min(quantum, process.remaining_time)
                self.gantt_data.append((current_time, process.process_id, exec_time))
                
                process.remaining_time -= exec_time
                current_time += exec_time
                
                # Check for new arrivals during execution
                while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                    p = self.processes[process_index]
                    p.state = "READY"
                    ready_queue.append(p)
                    process_index += 1
                
                if process.remaining_time == 0:
                    process.state = "TERMINATED"
                    process.completion_time = current_time
                    process.turnaround_time = current_time - process.arrival_time
                    process.waiting_time = process.turnaround_time - process.burst_time
                    self.completed_processes.append(process)
                    self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
                else:
                    # Re-add to queue
                    process.state = "READY"
                    ready_queue.append(process)
            else:
                current_time += 1
            
            time.sleep(0.01)
    
    def simulate_priority(self, preemptive=False):
        """Priority Scheduling (lower priority number = higher priority)"""
        ready_queue = []
        current_time = 0
        process_index = 0
        current_process = None
        
        while len(self.completed_processes) < len(self.processes) or (preemptive and current_process):
            if not self.simulation_running:
                break
            
            # Add newly arrived processes
            while process_index < len(self.processes) and self.processes[process_index].arrival_time <= current_time:
                p = self.processes[process_index]
                p.state = "READY"
                ready_queue.append(p)
                process_index += 1
            
            if preemptive and current_process:
                ready_queue.append(current_process)
            
            # Record metrics
            self.time_points.append(current_time)
            self.ready_queue_data.append(len(ready_queue))
            
            if ready_queue:
                # Sort by priority (lower number = higher priority)
                ready_queue.sort(key=lambda p: p.priority)
                process = ready_queue.pop(0)
                
                if process.start_time is None:
                    process.start_time = current_time
                    process.response_time = current_time - process.arrival_time
                
                process.state = "RUNNING"
                
                if preemptive:
                    # Execute for 1 time unit
                    exec_time = 1
                    self.gantt_data.append((current_time, process.process_id, exec_time))
                    process.remaining_time -= 1
                    current_time += 1
                    
                    if process.remaining_time == 0:
                        process.state = "TERMINATED"
                        process.completion_time = current_time
                        process.turnaround_time = current_time - process.arrival_time
                        process.waiting_time = process.turnaround_time - process.burst_time
                        self.completed_processes.append(process)
                        current_process = None
                        self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
                    else:
                        current_process = process
                else:
                    # Non-preemptive: execute till completion
                    self.gantt_data.append((current_time, process.process_id, process.burst_time))
                    current_time += process.burst_time
                    
                    process.state = "TERMINATED"
                    process.completion_time = current_time
                    process.turnaround_time = current_time - process.arrival_time
                    process.waiting_time = process.turnaround_time - process.burst_time
                    self.completed_processes.append(process)
                    self.status_var.set(f"Time: {current_time}ms | Completed: {len(self.completed_processes)}/{len(self.processes)}")
            else:
                current_time += 1
                if preemptive:
                    current_process = None
            
            time.sleep(0.005 if preemptive else 0.01)
    
    def update_plots(self, frame):
        if not self.time_points:
            return
        
        # Update ready queue plot
        self.ax_ready_queue.clear()
        self.ax_ready_queue.plot(self.time_points, self.ready_queue_data, 'b-', linewidth=2)
        self.ax_ready_queue.fill_between(self.time_points, self.ready_queue_data, alpha=0.3)
        self.ax_ready_queue.set_title('Ready Queue Length Over Time')
        self.ax_ready_queue.set_xlabel('Time (ms)')
        self.ax_ready_queue.set_ylabel('Processes in Ready Queue')
        self.ax_ready_queue.grid(True, alpha=0.3)
        
        # Update timeline plot
        self.ax_timeline.clear()
        if self.completed_processes:
            completion_times = [p.completion_time for p in self.completed_processes]
            self.ax_timeline.step(completion_times, range(1, len(completion_times) + 1), 
                                 'g-', linewidth=2, where='post')
        
        self.ax_timeline.set_title('Cumulative Processes Completed')
        self.ax_timeline.set_xlabel('Time (ms)')
        self.ax_timeline.set_ylabel('Processes Completed')
        self.ax_timeline.grid(True, alpha=0.3)
        
        self.canvas_live.draw()
    
    def show_results(self):
        if not self.completed_processes:
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "No processes completed.")
            return
        
        # Calculate metrics
        throughput = len(self.completed_processes)
        avg_waiting_time = statistics.mean([p.waiting_time for p in self.completed_processes])
        avg_turnaround_time = statistics.mean([p.turnaround_time for p in self.completed_processes])
        avg_response_time = statistics.mean([p.response_time for p in self.completed_processes if p.response_time is not None])
        
        total_time = max([p.completion_time for p in self.completed_processes])
        total_burst = sum([p.burst_time for p in self.completed_processes])
        cpu_utilization = (total_burst / total_time) * 100 if total_time > 0 else 0
        
        # Display results
        algo_names = {
            "fcfs": "First Come First Serve (FCFS)",
            "sjf": "Shortest Job First (SJF)",
            "srtf": "Shortest Remaining Time First (SRTF)",
            "rr": "Round Robin (RR)",
            "priority": "Priority Scheduling (Non-Preemptive)",
            "priority_preemptive": "Priority Scheduling (Preemptive)"
        }
        
        algo_name = algo_names.get(self.algorithm_var.get(), "Unknown")
        
        results_text = f"""
⚙️ PROCESS SCHEDULING RESULTS
{'='*60}
Algorithm: {algo_name}
Total Processes: {len(self.processes)}

📊 PERFORMANCE METRICS:
• Throughput: {throughput} processes completed
• Average Waiting Time: {avg_waiting_time:.2f} ms
• Average Turnaround Time: {avg_turnaround_time:.2f} ms
• Average Response Time: {avg_response_time:.2f} ms

⚡ CPU METRICS:
• Total Execution Time: {total_time} ms
• CPU Utilization: {cpu_utilization:.1f}%
• Context Switches: {len(self.gantt_data)}

📋 PROCESS DETAILS:
"""
        
        # Add individual process details
        for p in self.completed_processes[:10]:  # Show first 10
            results_text += f"  P{p.process_id}: Arrival={p.arrival_time}ms, Burst={p.burst_time}ms, "
            results_text += f"Wait={p.waiting_time}ms, TAT={p.turnaround_time}ms, Priority={p.priority}\n"
        
        if len(self.completed_processes) > 10:
            results_text += f"  ... and {len(self.completed_processes) - 10} more processes\n"
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, results_text)
        
        # Update results plots
        self.plot_results_charts()
        
        # Update Gantt chart
        self.plot_gantt_chart()
        
        self.simulation_running = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Simulation completed!")
    
    def plot_results_charts(self):
        """Plot performance analysis charts"""
        # Clear all result plots
        for ax in [self.ax_throughput, self.ax_waiting, self.ax_turnaround, self.ax_response]:
            ax.clear()
        
        # Throughput chart
        self.ax_throughput.bar(['Processes\nCompleted'], [len(self.completed_processes)], 
                              color='skyblue', alpha=0.7, edgecolor='navy', linewidth=2)
        self.ax_throughput.set_title('Throughput', fontweight='bold')
        self.ax_throughput.set_ylabel('Count')
        
        # Waiting time distribution
        waiting_times = [p.waiting_time for p in self.completed_processes]
        self.ax_waiting.hist(waiting_times, bins=min(20, len(self.completed_processes)), 
                            color='orange', alpha=0.7, edgecolor='darkorange')
        avg_wait = statistics.mean(waiting_times)
        self.ax_waiting.axvline(avg_wait, color='red', linestyle='--', linewidth=2,
                               label=f'Avg: {avg_wait:.1f}ms')
        self.ax_waiting.set_title('Waiting Time Distribution', fontweight='bold')
        self.ax_waiting.set_xlabel('Time (ms)')
        self.ax_waiting.set_ylabel('Frequency')
        self.ax_waiting.legend()
        
        # Turnaround time distribution
        turnaround_times = [p.turnaround_time for p in self.completed_processes]
        self.ax_turnaround.hist(turnaround_times, bins=min(20, len(self.completed_processes)), 
                               color='green', alpha=0.7, edgecolor='darkgreen')
        avg_tat = statistics.mean(turnaround_times)
        self.ax_turnaround.axvline(avg_tat, color='red', linestyle='--', linewidth=2,
                                  label=f'Avg: {avg_tat:.1f}ms')
        self.ax_turnaround.set_title('Turnaround Time Distribution', fontweight='bold')
        self.ax_turnaround.set_xlabel('Time (ms)')
        self.ax_turnaround.set_ylabel('Frequency')
        self.ax_turnaround.legend()
        
        # Response time chart
        response_times = [p.response_time for p in self.completed_processes if p.response_time is not None]
        if response_times:
            self.ax_response.hist(response_times, bins=min(20, len(response_times)), 
                                 color='purple', alpha=0.7, edgecolor='indigo')
            avg_resp = statistics.mean(response_times)
            self.ax_response.axvline(avg_resp, color='red', linestyle='--', linewidth=2,
                                    label=f'Avg: {avg_resp:.1f}ms')
            self.ax_response.set_title('Response Time Distribution', fontweight='bold')
            self.ax_response.set_xlabel('Time (ms)')
            self.ax_response.set_ylabel('Frequency')
            self.ax_response.legend()
        
        self.fig_results.tight_layout()
        self.canvas_results.draw()
    
    def plot_gantt_chart(self):
        """Create Gantt chart showing process execution timeline"""
        self.ax_gantt.clear()
        
        if not self.gantt_data:
            return
        
        # Consolidate consecutive executions of same process
        consolidated = []
        current_start = self.gantt_data[0][0]
        current_pid = self.gantt_data[0][1]
        current_duration = self.gantt_data[0][2]
        
        for i in range(1, len(self.gantt_data)):
            start, pid, duration = self.gantt_data[i]
            
            if pid == current_pid and start == current_start + current_duration:
                # Same process, consecutive execution
                current_duration += duration
            else:
                # Different process or gap, save current and start new
                consolidated.append((current_start, current_pid, current_duration))
                current_start = start
                current_pid = pid
                current_duration = duration
        
        # Add last segment
        consolidated.append((current_start, current_pid, current_duration))
        
        # Plot Gantt chart
        colors = plt.cm.tab20(np.linspace(0, 1, len(self.processes)))
        process_colors = {p.process_id: colors[i % len(colors)] for i, p in enumerate(self.processes)}
        
        y_pos = 0
        for start, pid, duration in consolidated:
            self.ax_gantt.barh(y_pos, duration, left=start, height=0.8, 
                              color=process_colors[pid], edgecolor='black', linewidth=0.5)
            # Add process label
            self.ax_gantt.text(start + duration/2, y_pos, f'P{pid}', 
                              ha='center', va='center', fontweight='bold', fontsize=8)
        
        self.ax_gantt.set_xlabel('Time (ms)', fontweight='bold')
        self.ax_gantt.set_ylabel('CPU', fontweight='bold')
        self.ax_gantt.set_title('Process Execution Gantt Chart', fontweight='bold', fontsize=12)
        self.ax_gantt.set_yticks([y_pos])
        self.ax_gantt.set_yticklabels(['CPU'])
        self.ax_gantt.grid(True, axis='x', alpha=0.3)
        
        # Add legend
        legend_elements = [plt.Rectangle((0,0),1,1, facecolor=process_colors[p.process_id], 
                                        edgecolor='black', label=f'P{p.process_id}')
                          for p in self.processes[:10]]  # Show first 10 in legend
        if len(self.processes) > 10:
            self.ax_gantt.legend(handles=legend_elements, loc='upper right', 
                                bbox_to_anchor=(1.15, 1), ncol=2, fontsize=8)
        else:
            self.ax_gantt.legend(handles=legend_elements, loc='upper right', 
                                bbox_to_anchor=(1.12, 1), fontsize=8)
        
        self.fig_gantt.tight_layout()
        self.canvas_gantt.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProcessSchedulerGUI(root)
    root.mainloop()