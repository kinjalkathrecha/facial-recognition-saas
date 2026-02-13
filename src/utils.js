import { Responsive } from "semantic-ui-react";
import axios from "axios";
import { APIEndpoint } from "./constants";

export const getWidth = () => {
    const isSSR = typeof window === "undefined";
    return isSSR ? Responsive.onlyTablet.minWidth : window.innerWidth;
};

// 1. Create the instance without the headers first
export const authAxios = axios.create({
    baseURL: APIEndpoint
});

// 2. Add a request interceptor
authAxios.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("token");
        if (token) {
            // Set the header dynamically for every request
            config.headers.Authorization = `Token ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);