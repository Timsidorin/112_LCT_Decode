import axios from "axios";

export class BaseApi {
        _baseUrl = "";
        _sourceUrl = "";
        _httpMethod = "";
        _data = {};
        _params = {};
        _axiosInstance = null;
        _headers = {};

        constructor(baseUrl) {
                this._baseUrl = baseUrl;
                this._axiosInstance = axios.create({
                        baseURL: this._baseUrl, // Исправлено: добавлено подчёркивание
                });
        }

        set httpMethod(method) {
                let allowedMethods = ["get", "post", "put", "delete", "patch"];
                if (allowedMethods.includes(method.toLowerCase())) {
                        this._httpMethod = method.toLowerCase();
                } else {
                        throw new Error(`Разрешенные методы (${allowedMethods.join(", ")})`);
                }
        }

        get httpMethod() {
                return this._httpMethod;
        }

        set data(data) {
                this._data = data;
        }

        get data() {
                return this._data;
        }

        set sourceUrl(url) {
                this._sourceUrl = url;
        }

        get sourceUrl() {
                return this._sourceUrl;
        }

        set params(params) {
                this._params = params;
        }

        get params() {
                return this._params;
        }

        set headers(headers) {
                this._headers = headers;
        }

        get headers() {
                return this._headers;
        }

        async request() {
                try {
                        const response = await this._axiosInstance({
                                method: this._httpMethod,
                                url: this._sourceUrl,
                                data: this._data,
                                params: this._params,
                                headers: this._headers
                        });
                        return response.data;
                } catch (error) {
                        throw error;
                }
        }
}
