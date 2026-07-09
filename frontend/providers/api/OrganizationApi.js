import { BaseApi } from "./BaseAPi.js";

export class OrganizationApi extends BaseApi {
	constructor() {
		super(__BASE__URL__);
	}

	list() {
		super.params = {};
		super.httpMethod = "get";
		super.sourceUrl = "/organizations";
		return super.createRequest();
	}

	create(payload) {
		super.params = {};
		super.httpMethod = "post";
		super.sourceUrl = "/organizations";
		super.data = payload;
		return super.createRequest();
	}

	get(orgId) {
		super.params = {};
		super.httpMethod = "get";
		super.sourceUrl = `/organizations/${orgId}`;
		return super.createRequest();
	}

	update(orgId, payload) {
		super.params = {};
		super.httpMethod = "patch";
		super.sourceUrl = `/organizations/${orgId}`;
		super.data = payload;
		return super.createRequest();
	}

	delete(orgId) {
		super.params = {};
		super.httpMethod = "delete";
		super.sourceUrl = `/organizations/${orgId}`;
		return super.createRequest();
	}

	addTraining(orgId, trainingUuid) {
		super.params = {};
		super.httpMethod = "post";
		super.sourceUrl = `/organizations/${orgId}/trainings/${trainingUuid}`;
		return super.createRequest();
	}

	removeTraining(orgId, trainingUuid) {
		super.params = {};
		super.httpMethod = "delete";
		super.sourceUrl = `/organizations/${orgId}/trainings/${trainingUuid}`;
		return super.createRequest();
	}

	addEmployee(orgId, payload) {
		super.params = {};
		super.httpMethod = "post";
		super.sourceUrl = `/organizations/${orgId}/employees`;
		super.data = payload;
		return super.createRequest();
	}

	addEmployeesBulk(orgId, employees) {
		super.params = {};
		super.httpMethod = "post";
		super.sourceUrl = `/organizations/${orgId}/employees/bulk`;
		super.data = { employees };
		return super.createRequest();
	}

	deleteEmployee(orgId, employeeId) {
		super.params = {};
		super.httpMethod = "delete";
		super.sourceUrl = `/organizations/${orgId}/employees/${employeeId}`;
		return super.createRequest();
	}

	deleteAllEmployees(orgId) {
		super.params = {};
		super.httpMethod = "delete";
		super.sourceUrl = `/organizations/${orgId}/employees`;
		return super.createRequest();
	}

	generateAccounts(orgId, regenerate = false, payload = {}) {
		super.params = regenerate ? { regenerate: true } : {};
		super.httpMethod = "post";
		super.sourceUrl = `/organizations/${orgId}/employees/generate-accounts`;
		super.data = payload;
		return super.createRequest();
	}

	assignedTrainings() {
		super.params = {};
		super.httpMethod = "get";
		super.sourceUrl = "/organizations/assigned-trainings";
		return super.createRequest();
	}
}

export const organizationApi = new OrganizationApi();
