import React, { Component, ErrorInfo, ReactNode } from "react";
import { Container, Header, Icon, Message, Segment } from "semantic-ui-react";

interface ErrorBoundaryProps {
  children: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component for graceful error handling
 * Catches JavaScript errors anywhere in the child component tree
 */
class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });
    this.props.onError?.(error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <Container style={{ marginTop: "2em" }}>
          <Segment placeholder textAlign="center">
            <Header icon>
              <Icon name="warning sign" color="red" />
              Something went wrong
            </Header>
            <Message negative>
              <Message.Header>Application Error</Message.Header>
              <p>
                {this.state.error?.message ?? "An unexpected error occurred"}
              </p>
              {process.env.NODE_ENV === "development" &&
                this.state.errorInfo && (
                  <pre className="error-stack-trace">
                    {this.state.errorInfo.componentStack}
                  </pre>
                )}
            </Message>
          </Segment>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
