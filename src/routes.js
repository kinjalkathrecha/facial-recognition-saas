import React from "react";
import { Route, Redirect, Switch } from "react-router-dom"; // Cleaned up imports
import Hoc from "./hoc/hoc";
import Login from "./containers/Login";
import Signup from "./containers/Signup";
import LandingPage from "./containers/LandingPage";
import demo from "./containers/demo";

// Added 'return' before the ternary operator
const PrivateRoute = ({ component: Component, ...rest }) => {
  const authenticated = localStorage.getItem("token") !== null;
  return (
    <Route
      {...rest}
      render={props =>
        authenticated ? (
          <Component {...props} />
        ) : (
          <Redirect to={{
            pathname: "/login",
            state: { from: props.location }
          }} />
        )
      }
    />
  );
};

const BaseRouter = () => (
  <Hoc>
    {/* It is highly recommended to wrap Routes in a <Switch> to prevent multiple matches */}
    <Switch>
      <Route exact path="/" component={LandingPage} />
      <Route path="/login" component={Login} />
      <Route path="/signup" component={Signup} />
      <Route path="/demo" component={demo} />
      <PrivateRoute path="/account" component={LandingPage} />
    </Switch>
  </Hoc>
);

export default BaseRouter;