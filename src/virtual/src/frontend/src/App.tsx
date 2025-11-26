import axios, { AxiosError } from "axios";
import React, { useEffect, useState } from "react";
import {
  Button,
  Container,
  Form,
  Grid,
  Header,
  Icon,
  Menu,
  Message,
  Segment,
} from "semantic-ui-react";

/** Service status response from the API */
interface ServiceStatus {
  service: string;
  version: string;
  healthy?: boolean;
}

/** Query response from the semantic API */
interface QueryResponse {
  response: string;
  success?: boolean;
}

/** Error response from the API */
interface ApiErrorResponse {
  message?: string;
  error?: string;
}

const App: React.FC = () => {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState<ServiceStatus | null>(null);

  useEffect(() => {
    void fetchStatus();
  }, []);

  const fetchStatus = async (): Promise<void> => {
    try {
      const result = await axios.get<ServiceStatus>("/api/semantic/status");
      setStatus(result.data);
    } catch (err) {
      const axiosError = err as AxiosError;
      console.error("Failed to fetch status", axiosError.message);
    }
  };

  const handleSubmit = async (): Promise<void> => {
    if (!query.trim()) {
      setError("Please enter a query");
      return;
    }

    setLoading(true);
    setError("");
    setResponse("");

    try {
      const result = await axios.post<QueryResponse>("/api/semantic/query", {
        query,
      });
      setResponse(result.data.response);
    } catch (err) {
      const axiosError = err as AxiosError<ApiErrorResponse>;
      const errorMessage =
        axiosError.response?.data?.message ??
        axiosError.response?.data?.error ??
        axiosError.message ??
        "An error occurred";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container style={{ marginTop: "2em" }}>
      <Menu fixed="top" inverted role="navigation" aria-label="Main navigation">
        <Container>
          <Menu.Item header>
            <Icon name="lightbulb outline" aria-hidden="true" />
            Semantic Kernel App
          </Menu.Item>
          {status && (
            <Menu.Item
              position="right"
              aria-label={`Service status: ${status.service} version ${status.version}`}
            >
              <Icon name="circle" color="green" aria-hidden="true" />
              {status.service} v{status.version}
            </Menu.Item>
          )}
        </Container>
      </Menu>

      <Grid style={{ marginTop: "5em" }} role="main" aria-label="Main content">
        <Grid.Row>
          <Grid.Column width={16}>
            <Header as="h1" textAlign="center">
              <Icon name="lightbulb outline" aria-hidden="true" />
              <Header.Content>
                Semantic Kernel Query Interface
                <Header.Subheader>
                  Powered by AI and Vector Search
                </Header.Subheader>
              </Header.Content>
            </Header>
          </Grid.Column>
        </Grid.Row>

        <Grid.Row>
          <Grid.Column width={16}>
            <Segment raised>
              <Form onSubmit={handleSubmit} aria-label="Query submission form">
                <Form.TextArea
                  id="query-input"
                  label="Enter your query"
                  placeholder="Ask me anything about your semantic data..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  rows={4}
                  aria-required="true"
                  aria-describedby="query-help"
                />
                <span id="query-help" className="sr-only">
                  Type your question about semantic data
                </span>
                <Button
                  primary
                  type="submit"
                  loading={loading}
                  disabled={loading || !query.trim()}
                  icon
                  labelPosition="left"
                  aria-label={loading ? "Submitting query..." : "Submit query"}
                >
                  <Icon name="send" aria-hidden="true" />
                  Submit Query
                </Button>
              </Form>
            </Segment>
          </Grid.Column>
        </Grid.Row>

        {error && (
          <Grid.Row>
            <Grid.Column width={16}>
              <Message negative icon role="alert" aria-live="assertive">
                <Icon name="warning circle" aria-hidden="true" />
                <Message.Content>
                  <Message.Header as="h2">Error</Message.Header>
                  {error}
                </Message.Content>
              </Message>
            </Grid.Column>
          </Grid.Row>
        )}

        {response && (
          <Grid.Row>
            <Grid.Column width={16}>
              <Message positive icon role="status" aria-live="polite">
                <Icon name="check circle" aria-hidden="true" />
                <Message.Content>
                  <Message.Header as="h2">Response</Message.Header>
                  <p>{response}</p>
                </Message.Content>
              </Message>
            </Grid.Column>
          </Grid.Row>
        )}

        <Grid.Row>
          <Grid.Column width={16}>
            <Segment secondary as="section" aria-labelledby="about-heading">
              <Header as="h2" id="about-heading">
                <Icon name="info circle" aria-hidden="true" />
                About
              </Header>
              <p>
                This application uses Semantic Kernel to process natural
                language queries, generate embeddings, and perform vector
                similarity searches across your data.
              </p>
              <p>
                <strong>Features:</strong>
              </p>
              <ul aria-label="Application features">
                <li>Natural language query processing</li>
                <li>Vector embeddings with OpenAI</li>
                <li>Qdrant vector database integration</li>
                <li>Real-time semantic search</li>
              </ul>
            </Segment>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </Container>
  );
};

export default App;
