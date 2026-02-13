import React, { useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import {
    CardElement,
    Elements,
    useStripe,
    useElements,
} from "@stripe/react-stripe-js";
import { Divider, Button, Message } from "semantic-ui-react";
import { authAxios } from "../../utils";
import { subscribeURL } from "../../constants";

// Initialize Stripe outside the component to prevent re-initialization on every render
const stripePromise = loadStripe("pk_test_51Sx32dFHM7GWRJu8g78JHgFcsYl96njMLO95CH22NQZ8Chli38d7wr9feLkSbTBEE2OaC7x076jb5lgmUHyVlxog00pOMwohux");

const StripeForm = (props) => {
    const stripe = useStripe();
    const elements = useElements();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError(null);

        if (!stripe || !elements) {
            // Stripe.js has not loaded yet.
            setLoading(false);
            return;
        }

        // 1. Get a reference to the mounted CardElement
        const cardElement = elements.getElement(CardElement);

        // 2. Create the token
        const { error: stripeError, token } = await stripe.createToken(cardElement);

        if (stripeError) {
            setError(stripeError.message);
            setLoading(false);
        } else {
            // 3. Send token to your backend via Axios
            try {
                await authAxios.post(subscribeURL, {
                    stripeToken: token.id,
                });
                setLoading(false);
                props.handleUserDetails(); // Callback to refresh user state
            } catch (err) {
                console.error(err);
                setLoading(false);
                // The optional chaining (?.) prevents the "undefined" crash
                setError(err.response?.data?.message || "An error occurred with the payment.");
            }
        }
    };

    return (
        <React.Fragment>
            <Divider />
            {error && <Message error header="There was an error" content={error} />}

            <div style={{ padding: "10px", border: "1px solid #ccc", borderRadius: "4px" }}>
                <CardElement options={{ style: { base: { fontSize: "16px" } } }} />
            </div>

            <Button
                primary
                style={{ marginTop: "10px" }}
                loading={loading}
                disabled={!stripe || loading}
                onClick={handleSubmit}
            >
                Go pro
            </Button>
        </React.Fragment>
    );
};

// 4. The Parent Wrapper
const SubscribeForm = (props) => {
    return (
        <Elements stripe={stripePromise}>
            <div style={{ maxWidth: "400px", margin: "0 auto" }}>
                <StripeForm {...props} />
            </div>
        </Elements>
    );
};

export default SubscribeForm;