import { createMedia } from '@artsy/fresnel'
import PropTypes from 'prop-types'
import React, { Component } from 'react'
import { InView } from 'react-intersection-observer'
import {
    Button,
    Container,
    Menu,
    Segment,
    Sidebar,
} from 'semantic-ui-react'
import { Link, withRouter } from "react-router-dom";

import { getWidth } from "../../utils";

import { Media } from '../media'

export { Media }

class DesktopContainer extends Component {
    state = {}

    toggleFixedMenu = (inView) => this.setState({ fixed: !inView })

    render() {
        const { children } = this.props
        const { fixed } = this.state

        return (
            <Media greaterThan='mobile'>
                <InView onChange={this.toggleFixedMenu}>
                    <Segment
                        inverted
                        textAlign='center'
                        style={{ padding: '1em 0em' }}
                        vertical
                    >
                        <Menu
                            fixed={fixed ? 'top' : null}
                            inverted={!fixed}
                            pointing={!fixed}
                            secondary={!fixed}
                            size='large'
                        >
                            <Container>
                                <Menu.Item
                                    as='a'
                                    active
                                    onClick={() => this.props.history.push("/")}
                                >
                                    Home
                                </Menu.Item>
                                <Menu.Item as='a' onClick={() => this.props.history.push("/demo")}>Demo</Menu.Item>
                                <Menu.Item position='right'>
                                    <Button as='a' inverted={!fixed} onClick={() => this.props.history.push("/login")}>
                                        Log in
                                    </Button>
                                    <Button as='a' inverted={!fixed} primary={fixed} style={{ marginLeft: '0.5em' }}
                                        onClick={() => this.props.history.push("/signup")}
                                    >
                                        Sign Up
                                    </Button>
                                </Menu.Item>
                            </Container>
                        </Menu>
                    </Segment>
                </InView>

                {children}
            </Media>
        )
    }
}

DesktopContainer.propTypes = {
    children: PropTypes.node,
}

export default withRouter(DesktopContainer);