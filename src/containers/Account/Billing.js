import React from "react";
import {
    Header,
    Divider,
    Segment,
    Icon,
    Dimmer,
    Loader,
    Image,
    Button
} from "semantic-ui-react";
import Shell from "./shell";
import short_paragraph from '../../assets/images/short_paragraph.png';
import SubscribeForm from "./SubscribeForm";
import { authAxios } from "../../utils";
import { billingURL } from "../../constants";

class Billing extends React.Component {
    state = {
        error: null,
        loading: false,
        billingDetails: null // Changed from {} to null for easier conditional checking
    };

    componentDidMount() {
        this.handleUserDetails();
    }

    handleUserDetails = () => {
        this.setState({ loading: true, error: null });
        authAxios
            .get(billingURL)
            .then(res => {
                this.setState({
                    loading: false,
                    billingDetails: res.data
                });
            })
            .catch(err => {
                this.setState({
                    loading: false,
                    // Use optional chaining to prevent the "reading data of undefined" error
                    error: err.response?.data?.message || "Failed to fetch billing details."
                });
            });
    };

    renderBillingDetails(details) {
        // Guard clause: if details is null or hasn't loaded membershipType, show nothing or a loader
        if (!details || !details.membershipType) return null;

        const { membershipType } = details;
        const free_trial = "free_trial";
        const member = "member";
        const not_member = "not_member";

        return (
            <Segment>
                <Header as='h3'>Monthly Summary</Header>
                {membershipType === free_trial && (
                    <React.Fragment>
                        <p>Your free trial ends on {details.endDate || '19 june 2029'}</p>
                        <p>API requests this month: {details.apiRequests || 0}</p>
                        <SubscribeForm handleUserDetails={this.handleUserDetails} />
                    </React.Fragment>
                )}
                {membershipType === member && (
                    <React.Fragment>
                        <p>Next billing date: {details.nextBillingDate || '25 june 2029'}</p>
                        <p>API requests this month: {details.apiRequests || 0}</p>
                        <p>Amount due: ${details.amountDue || 0}</p>
                    </React.Fragment>
                )}
                {membershipType === not_member && (
                    <React.Fragment>
                        <p>Your free trial has ended</p>
                        <SubscribeForm handleUserDetails={this.handleUserDetails} />
                    </React.Fragment>
                )}
            </Segment>
        );
    }

    render() {
        const { loading, error, billingDetails } = this.state;

        return (
            <Shell>
                {/* Error State */}
                {error && (
                    <Segment placeholder>
                        <Header icon>
                            <Icon name="warning sign" />
                            {error}
                        </Header>
                        <Button primary onClick={this.handleUserDetails}>Try Again</Button>
                    </Segment>
                )}

                {/* Loading State */}
                {loading && (
                    <Segment>
                        <Dimmer active inverted>
                            <Loader inverted>Loading billing details...</Loader>
                        </Dimmer>
                        <Image src={short_paragraph} />
                    </Segment>
                )}

                {/* Data State: Only render if not loading and we have details */}
                {!loading && billingDetails && this.renderBillingDetails(billingDetails)}
            </Shell>
        );
    }
}

export default Billing;