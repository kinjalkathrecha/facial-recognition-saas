let DEBUG = true;
let host = "http://127.0.0.1:8000";
let stripePublishKey = "pk_test_51Sx32dFHM7GWRJu8g78JHgFcsYl96njMLO95CH22NQZ8Chli38d7wr9feLkSbTBEE2OaC7x076jb5lgmUHyVlxog00pOMwohux";
if (!DEBUG) {
    host = "https://domain.com";
    let stripePublishKey = "pk_test_51Sx32dFHM7GWRJu8g78JHgFcsYl96njMLO95CH22NQZ8Chli38d7wr9feLkSbTBEE2OaC7x076jb5lgmUHyVlxog00pOMwohux";
}

export { stripePublishKey };

export const APIEndpoint = `${host}/api`;

export const fileUploadURL = `${APIEndpoint}/demo/`;
export const facialRecognitionURL = `${APIEndpoint}/upload/`;
export const emailURL = `${APIEndpoint}/email/`;
export const changeEmailURL = `${APIEndpoint}/change-email/`;
export const changePasswordURL = `${APIEndpoint}/change-password/`;
export const billingURL = `${APIEndpoint}/billing/`;
export const subscribeURL = `${APIEndpoint}/subscribe/`;
export const APIkeyURL = `${APIEndpoint}/api-key/`;