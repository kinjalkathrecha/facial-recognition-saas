import React from "react";
import {
  Button,
  Form,
  Grid,
  Header,
  Message,
  Segment
} from "semantic-ui-react";
import { MessageHeader } from 'semantic-ui-react'
import { connect } from "react-redux";
import { NavLink, Redirect } from "react-router-dom";
import { authSignup as signup } from "../store/actions/auth";

class RegistrationForm extends React.Component {
  state = {
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    formError: null
  };

  handleSubmit = e => {
    e.preventDefault();
    const { username, email, password, confirmPassword } = this.state;
    if (
      username !== "" &&
      email !== "" &&
      password !== "" &&
      confirmPassword !== "" &&
      this.comparePasswords() === true &&
      this.comparePasswordLengths() === true
    )
      this.props.signup(username, email, password, confirmPassword);

  };

  comparePasswords = () => {
    const { password, confirmPassword } = this.state;
    if (password !== confirmPassword) {
      this.setState({ formError: "Your passwords do not match" });
      return false;
    } else {
      return true;
    }
  };

  comparePasswordLengths = () => {
    const { password, confirmPassword } = this.state;
    if (password.length >= 6 && confirmPassword.length >= 6) {
      return true;
    } else {
      this.setState({
        formError: "Your password must be a minimum of 6 characters"
      });
      return false;
    }
  };


  handleChange = e => {
    this.setState({
      [e.target.name]: e.target.value,
      formError: null
    });
  };

  render() {
    const { formError } = this.state;
    const { error, loading, authenticated } = this.props;
    const { username, email, password1, password2 } = this.state;
    if (authenticated) {
      return <Redirect to="/" />;
    }
    return (
      <Grid
        textAlign="center"
        style={{ height: "100vh" }}
        verticalAlign="middle"
      >
        <Grid.Column style={{ maxWidth: 450 }}>
          <Header as="h2" color="teal" textAlign="center">
            Signup to your account
          </Header>
          {error && <p>{this.props.error.message}</p>}

          <React.Fragment>
            <Form size="large" onSubmit={this.handleSubmit}>
              <Segment stacked>
                <Form.Input
                  onChange={this.handleChange}
                  value={username}
                  name="username"
                  fluid
                  icon="user"
                  iconPosition="left"
                  placeholder="Username"
                />
                <Form.Input
                  onChange={this.handleChange}
                  value={email}
                  name="email"
                  type="email"
                  fluid
                  icon="mail"
                  iconPosition="left"
                  placeholder="E-mail address"
                />
                <Form.Input
                  onChange={this.handleChange}
                  fluid
                  value={password1}
                  name="password"
                  icon="lock"
                  iconPosition="left"
                  placeholder="Password"
                  type="password"
                />
                <Form.Input
                  onChange={this.handleChange}
                  fluid
                  value={password2}
                  name="confirmPassword"
                  icon="lock"
                  iconPosition="left"
                  placeholder="Confirm password"
                  type="password"
                />

                <Button
                  color="teal"
                  fluid
                  size="large"
                  loading={loading}
                  disabled={loading}
                >
                  Signup
                </Button>
              </Segment>
            </Form>
            {formError && (
              <Message negative>
                <MessageHeader>There was an error</MessageHeader>
                <p>{formError}</p>
              </Message>
            )}
            {error && (
              <Message negative>
                <MessageHeader>There was an error</MessageHeader>
                <p>{error}</p>
              </Message>
            )}
            <Message>
              Already have an account? <NavLink to="/login">Login</NavLink>
            </Message>
          </React.Fragment>
        </Grid.Column>
      </Grid>
    );
  }
}

const mapStateToProps = state => {
  return {
    loading: state.auth.loading,
    error: state.auth.error,
    authenticated: state.auth.token !== null
  };
};

const mapDispatchToProps = dispatch => {
  return {
    signup: (username, email, password1, password2) =>
      dispatch(signup(username, email, password1, password2))
  };
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(RegistrationForm);
