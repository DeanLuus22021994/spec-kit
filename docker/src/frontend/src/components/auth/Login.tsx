import axios, { AxiosError } from "axios";
import React, { useCallback, useEffect, useState } from "react";
import {
  Button,
  Container,
  Divider,
  Form,
  Grid,
  Header,
  Icon,
  Input,
  Message,
  Segment,
} from "semantic-ui-react";

// ============================================================================
// Types
// ============================================================================

interface LoginCredentials {
  email: string;
  password: string;
}

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  avatar?: string;
}

interface AuthResponse {
  token: string;
  refreshToken: string;
  user: User;
  expiresAt: string;
}

interface ApiError {
  message?: string;
  error?: string;
}

interface OAuthProvider {
  name: string;
  icon: "github" | "microsoft" | "google";
  color: "black" | "blue" | "red";
  url: string;
}

// ============================================================================
// Login Component
// ============================================================================

const Login: React.FC = () => {
  // State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  // OAuth providers
  const oauthProviders: OAuthProvider[] = [
    {
      name: "GitHub",
      icon: "github",
      color: "black",
      url: "/api/auth/oauth/github",
    },
    {
      name: "Microsoft",
      icon: "microsoft",
      color: "blue",
      url: "/api/auth/oauth/azure",
    },
  ];

  // Check for remembered email
  useEffect(() => {
    const remembered = localStorage.getItem("rememberedEmail");
    if (remembered) {
      setEmail(remembered);
      setRememberMe(true);
    }
  }, []);

  // ============================================================================
  // Handlers
  // ============================================================================

  const handleLogin = useCallback(
    async (e: React.FormEvent): Promise<void> => {
      e.preventDefault();
      setError(null);

      // Validation
      if (!email.trim()) {
        setError("Please enter your email address");
        return;
      }
      if (!password) {
        setError("Please enter your password");
        return;
      }

      setLoading(true);

      try {
        const credentials: LoginCredentials = { email, password };
        const response = await axios.post<AuthResponse>(
          "/api/auth/login",
          credentials,
        );

        // Store tokens
        sessionStorage.setItem("authToken", response.data.token);
        sessionStorage.setItem("refreshToken", response.data.refreshToken);
        sessionStorage.setItem("user", JSON.stringify(response.data.user));

        // Remember email if checked
        if (rememberMe) {
          localStorage.setItem("rememberedEmail", email);
        } else {
          localStorage.removeItem("rememberedEmail");
        }

        // Redirect to dashboard
        window.location.href = "/dashboard";
      } catch (err) {
        const axiosError = err as AxiosError<ApiError>;
        setError(
          axiosError.response?.data?.message ??
            axiosError.response?.data?.error ??
            "Login failed. Please check your credentials.",
        );
      } finally {
        setLoading(false);
      }
    },
    [email, password, rememberMe],
  );

  const handleOAuthLogin = (provider: OAuthProvider): void => {
    // Store current URL for redirect after OAuth
    sessionStorage.setItem("oauthRedirect", window.location.href);
    window.location.href = provider.url;
  };

  const handleForgotPassword = (): void => {
    // Navigate to forgot password page
    window.location.href = "/forgot-password";
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <Container>
      <Grid
        textAlign="center"
        style={{ height: "100vh" }}
        verticalAlign="middle"
      >
        <Grid.Column style={{ maxWidth: 450 }}>
          <Header as="h2" color="blue" textAlign="center">
            <Icon name="lightbulb outline" />
            Semantic Kernel Platform
          </Header>

          <Segment stacked>
            <Form size="large" onSubmit={handleLogin}>
              <Form.Field>
                <Input
                  fluid
                  icon="user"
                  iconPosition="left"
                  placeholder="Email address"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  autoComplete="email"
                  aria-label="Email address"
                />
              </Form.Field>
              <Form.Field>
                <Input
                  fluid
                  icon="lock"
                  iconPosition="left"
                  placeholder="Password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                  autoComplete="current-password"
                  aria-label="Password"
                  action={{
                    icon: showPassword ? "eye slash" : "eye",
                    onClick: () => setShowPassword(!showPassword),
                    type: "button",
                  }}
                />
              </Form.Field>
              <Form.Field>
                <Form.Checkbox
                  label="Remember me"
                  checked={rememberMe}
                  onChange={() => setRememberMe(!rememberMe)}
                />
              </Form.Field>

              {error && (
                <Message negative>
                  <Icon name="warning circle" />
                  {error}
                </Message>
              )}

              <Button
                color="blue"
                fluid
                size="large"
                type="submit"
                loading={loading}
                disabled={loading}
              >
                <Icon name="sign in" />
                Login
              </Button>
            </Form>

            <Divider horizontal>Or</Divider>

            {oauthProviders.map((provider) => (
              <Button
                key={provider.name}
                color={provider.color}
                fluid
                style={{ marginBottom: "0.5em" }}
                onClick={() => handleOAuthLogin(provider)}
                disabled={loading}
              >
                <Icon name={provider.icon} />
                Continue with {provider.name}
              </Button>
            ))}
          </Segment>

          <Message>
            <Button
              basic
              color="blue"
              onClick={handleForgotPassword}
              style={{ background: "transparent", boxShadow: "none" }}
            >
              Forgot password?
            </Button>
          </Message>

          <Segment secondary>
            <Header as="h4" textAlign="center">
              Enterprise Features
            </Header>
            <Grid columns={3} textAlign="center">
              <Grid.Column>
                <Icon name="shield" size="large" color="blue" />
                <p>Secure Auth</p>
              </Grid.Column>
              <Grid.Column>
                <Icon name="cogs" size="large" color="blue" />
                <p>Config Mgmt</p>
              </Grid.Column>
              <Grid.Column>
                <Icon name="chart line" size="large" color="blue" />
                <p>Analytics</p>
              </Grid.Column>
            </Grid>
          </Segment>
        </Grid.Column>
      </Grid>
    </Container>
  );
};

export default Login;
