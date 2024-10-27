package main

import (
	"cc-nms/lib"

	"encoding/json"
	"fmt"
	"io"
	"os"
)

// loadTasks reads the configuration file, parses it, and returns the tasks.
func loadTasks(filename string) ([]lib.Task, error) {
	file, err := os.Open(filename) // opens json file
	if err != nil {                //checks if there was a error opening the file
		return nil, err
	}
	defer file.Close()

	fileContent, err := io.ReadAll(file)
	if err != nil {
		return nil, err // Return an error if we can't read the file
	}

	// Create an instance of the struct task to hold the parsed data
	var tasks []lib.Task

	// Parse the JSON data into the struct task
	err = json.Unmarshal(fileContent, &tasks)
	if err != nil { //checks if there was a error decoding the task
		return nil, err
	}

	return tasks, nil
}

func main() {
	fmt.Println("Hello, from NMS Server!")

	tasks, err := loadTasks("tasks.json")
	if err != nil {
		fmt.Println("Error loading tasks:", err)
		return
	}

	fmt.Println("Tasks loaded successfully:")
	for _, task := range tasks { // _, because we don't need de index of the task
		fmt.Printf("Task ID: %s, Frequency: %d\n", task.Task_ID, task.Frequency)
		for _, device := range task.Devices {
			fmt.Printf("  Device ID: %s\n", device.Device_ID)
			fmt.Printf("  CPU Usage Monitoring: %t\n", device.Device_Metrics.CPU_Usage)
			fmt.Printf("  RAM Usage Monitoring: %t\n", device.Device_Metrics.RAM_Usage)
			fmt.Println("  Interface Stats:", device.Device_Metrics.Interface_Stats)
			fmt.Println("  Link Metrics:", device.Link_Metrics)
		}
	}
}
