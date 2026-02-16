import React, { useState } from "react";
import {
    CardElement,
    Elements,
    useStripe,
    useElements,
} from "@stripe/react-stripe-js";
// 1. Import loadStripe
import { loadStripe } from "@stripe/stripe-js";
import { Divider, Button, Message } from "semantic-ui-react";
import { authAxios } from "../../utils";
import { subscribeURL, stripePublishKey } from "../../constants";

// 2. Initialize Stripe OUTSIDE the component
const stripePromise = loadStripe(stripePublishKey);

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
            setLoading(false);
            return;
        }

        const cardElement = elements.getElement(CardElement);
        const { error: stripeError, token } = await stripe.createToken(cardElement);

        if (stripeError) {
            setError(stripeError.message);
            setLoading(false);
        } else {
            try {
                await authAxios.post(subscribeURL, {
                    stripeToken: token.id,
                });
                setLoading(false);
                props.handleUserDetails();
            } catch (err) {
                setLoading(false);
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

// 3. The Modern Parent Wrapper
const SubscribeForm = (props) => {
    return (
        /* Notice: No more StripeProvider. Elements now takes the stripe prop directly via the promise. */
        <Elements stripe={stripePromise}>
            <div style={{ maxWidth: "400px", margin: "0 auto" }}>
                <StripeForm {...props} />
            </div>
        </Elements>
    );
};

export default SubscribeForm;