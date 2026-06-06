import axios from "axios";

function authHeaders() {
	const token = localStorage.getItem("tokenAuth");
	return token ? { Authorization: `Bearer ${token}` } : {};
}

export class TasksApi {
	upload(file, onUploadProgress) {
		const formData = new FormData();
		formData.append("file", file);
		return axios.post(`${__BASE__URL__}/tasks/upload`, formData, {
			headers: {
				...authHeaders(),
				"Content-Type": "multipart/form-data",
			},
			onUploadProgress,
		});
	}

	getTask(taskId) {
		return axios.get(`${__BASE__URL__}/tasks/${taskId}`, {
			headers: authHeaders(),
		});
	}

	listTasks(activeOnly = false) {
		return axios.get(`${__BASE__URL__}/tasks/`, {
			headers: authHeaders(),
			params: activeOnly ? { active_only: true } : {},
		});
	}

	dismissActiveTasks() {
		return axios.post(`${__BASE__URL__}/tasks/active/dismiss`, null, {
			headers: authHeaders(),
		});
	}
}

export const tasksApi = new TasksApi();
