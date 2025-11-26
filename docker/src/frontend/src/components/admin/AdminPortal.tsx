import axios, { AxiosError } from "axios";
import React, { useCallback, useEffect, useState } from "react";
import {
  Accordion,
  Button,
  Container,
  Dimmer,
  Dropdown,
  Form,
  Grid,
  Header,
  Icon,
  Label,
  Loader,
  Menu,
  Message,
  Modal,
  Segment,
  Tab,
  Table,
} from "semantic-ui-react";

// ============================================================================
// Types
// ============================================================================

interface ConfigFile {
  name: string;
  path: string;
  lastModified: string;
  size: number;
  version: string;
}

interface ConfigContent {
  content: string;
  schema?: string;
  version: string;
  lastModified: string;
}

interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

interface ValidationError {
  line: number;
  column: number;
  message: string;
  severity: "error" | "warning";
}

interface ValidationWarning {
  line: number;
  message: string;
}

interface ServiceStatus {
  name: string;
  status: "running" | "stopped" | "error" | "starting";
  uptime: string;
  memory: string;
  cpu: string;
  port: number;
  healthCheck: boolean;
}

interface DeploymentHistory {
  id: string;
  timestamp: string;
  file: string;
  action: "deploy" | "rollback";
  user: string;
  status: "success" | "failed" | "pending";
}

interface ApiError {
  message?: string;
  error?: string;
}

// ============================================================================
// Admin Portal Component
// ============================================================================

const AdminPortal: React.FC = () => {
  // State
  const [activeTab, setActiveTab] = useState(0);
  const [configFiles, setConfigFiles] = useState<ConfigFile[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<string | null>(null);
  const [configContent, setConfigContent] = useState<string>("");
  const [originalContent, setOriginalContent] = useState<string>("");
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [deploymentHistory, setDeploymentHistory] = useState<
    DeploymentHistory[]
  >([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [validationResult, setValidationResult] =
    useState<ValidationResult | null>(null);
  const [message, setMessage] = useState<{
    type: "success" | "error" | "warning";
    text: string;
  } | null>(null);
  const [confirmModal, setConfirmModal] = useState<{
    open: boolean;
    action: string;
    onConfirm: () => void;
  }>({
    open: false,
    action: "",
    onConfirm: () => {},
  });

  // ============================================================================
  // API Functions
  // ============================================================================

  const fetchConfigFiles = useCallback(async () => {
    setLoading(true);
    try {
      const response = await axios.get<ConfigFile[]>("/api/admin/configs");
      setConfigFiles(response.data);
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      setMessage({
        type: "error",
        text:
          error.response?.data?.message ??
          "Failed to fetch configuration files",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchConfigContent = useCallback(async (filename: string) => {
    setLoading(true);
    try {
      const response = await axios.get<ConfigContent>(
        `/api/admin/configs/${encodeURIComponent(filename)}`,
      );
      setConfigContent(response.data.content);
      setOriginalContent(response.data.content);
      setSelectedConfig(filename);
      setValidationResult(null);
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      setMessage({
        type: "error",
        text: error.response?.data?.message ?? `Failed to load ${filename}`,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchServices = useCallback(async () => {
    try {
      const response = await axios.get<ServiceStatus[]>(
        "/api/admin/services/status",
      );
      setServices(response.data);
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      setMessage({
        type: "error",
        text: error.response?.data?.message ?? "Failed to fetch service status",
      });
    }
  }, []);

  const fetchDeploymentHistory = useCallback(async () => {
    try {
      const response = await axios.get<DeploymentHistory[]>(
        "/api/admin/deployments/history",
      );
      setDeploymentHistory(response.data);
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      setMessage({
        type: "error",
        text:
          error.response?.data?.message ?? "Failed to fetch deployment history",
      });
    }
  }, []);

  // ============================================================================
  // Action Handlers
  // ============================================================================

  const validateConfig = async (): Promise<void> => {
    if (!selectedConfig) return;

    setSaving(true);
    try {
      const response = await axios.post<ValidationResult>(
        `/api/admin/configs/${encodeURIComponent(selectedConfig)}/validate`,
        { content: configContent },
      );
      setValidationResult(response.data);
      setMessage({
        type: response.data.valid ? "success" : "warning",
        text: response.data.valid
          ? "Configuration is valid"
          : `Validation found ${response.data.errors.length} error(s)`,
      });
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      setMessage({
        type: "error",
        text: error.response?.data?.message ?? "Validation failed",
      });
    } finally {
      setSaving(false);
    }
  };

  const saveConfig = async (): Promise<void> => {
    if (!selectedConfig) return;

    setSaving(true);
    try {
      await axios.put(
        `/api/admin/configs/${encodeURIComponent(selectedConfig)}`,
        {
          content: configContent,
        },
      );
      setOriginalContent(configContent);
      setMessage({ type: "success", text: "Configuration saved successfully" });
      await fetchConfigFiles();
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      setMessage({
        type: "error",
        text: error.response?.data?.message ?? "Failed to save configuration",
      });
    } finally {
      setSaving(false);
    }
  };

  const deployConfig = async (): Promise<void> => {
    if (!selectedConfig) return;

    setSaving(true);
    try {
      await axios.post(
        `/api/admin/configs/${encodeURIComponent(selectedConfig)}/deploy`,
      );
      setMessage({
        type: "success",
        text: "Configuration deployed successfully with hot-reload",
      });
      await fetchDeploymentHistory();
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      setMessage({
        type: "error",
        text: error.response?.data?.message ?? "Deployment failed",
      });
    } finally {
      setSaving(false);
      setConfirmModal({ open: false, action: "", onConfirm: () => {} });
    }
  };

  const rollbackConfig = async (deploymentId: string): Promise<void> => {
    setSaving(true);
    try {
      await axios.post(`/api/admin/configs/rollback/${deploymentId}`);
      setMessage({ type: "success", text: "Rollback completed successfully" });
      await fetchDeploymentHistory();
      if (selectedConfig) {
        await fetchConfigContent(selectedConfig);
      }
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      setMessage({
        type: "error",
        text: error.response?.data?.message ?? "Rollback failed",
      });
    } finally {
      setSaving(false);
      setConfirmModal({ open: false, action: "", onConfirm: () => {} });
    }
  };

  const restartService = async (serviceName: string): Promise<void> => {
    try {
      await axios.post(`/api/admin/services/${serviceName}/restart`);
      setMessage({
        type: "success",
        text: `Service ${serviceName} restart initiated`,
      });
      await fetchServices();
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      setMessage({
        type: "error",
        text:
          error.response?.data?.message ?? `Failed to restart ${serviceName}`,
      });
    }
    setConfirmModal({ open: false, action: "", onConfirm: () => {} });
  };

  // ============================================================================
  // Effects
  // ============================================================================

  useEffect(() => {
    void fetchConfigFiles();
    void fetchServices();
    void fetchDeploymentHistory();

    // Poll services every 30 seconds
    const interval = setInterval(() => {
      void fetchServices();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchConfigFiles, fetchServices, fetchDeploymentHistory]);

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const hasChanges = configContent !== originalContent;

  const getStatusColor = (
    status: string,
  ): "green" | "red" | "yellow" | "orange" => {
    switch (status) {
      case "running":
        return "green";
      case "stopped":
        return "red";
      case "error":
        return "red";
      case "starting":
        return "yellow";
      default:
        return "orange";
    }
  };

  // ============================================================================
  // Tab Panes
  // ============================================================================

  const panes = [
    {
      menuItem: { key: "config", icon: "file code", content: "Configuration" },
      render: () => (
        <Tab.Pane>
          <Grid>
            <Grid.Column width={4}>
              <Segment>
                <Header as="h4">
                  <Icon name="folder open" />
                  Configuration Files
                </Header>
                <Menu vertical fluid>
                  {configFiles.map((file) => (
                    <Menu.Item
                      key={file.path}
                      active={selectedConfig === file.name}
                      onClick={() => fetchConfigContent(file.name)}
                    >
                      <Label color="blue">{file.version}</Label>
                      {file.name}
                    </Menu.Item>
                  ))}
                </Menu>
              </Segment>
            </Grid.Column>
            <Grid.Column width={12}>
              <Segment>
                {selectedConfig ? (
                  <>
                    <Header as="h4">
                      <Icon name="edit" />
                      {selectedConfig}
                      {hasChanges && (
                        <Label
                          color="orange"
                          size="small"
                          style={{ marginLeft: "1em" }}
                        >
                          Unsaved Changes
                        </Label>
                      )}
                    </Header>
                    <Form>
                      <Form.TextArea
                        value={configContent}
                        onChange={(e) => setConfigContent(e.target.value)}
                        rows={20}
                        style={{
                          fontFamily: "monospace",
                          fontSize: "13px",
                          lineHeight: "1.5",
                        }}
                      />
                    </Form>
                    <div className="admin-button-group">
                      <Button
                        primary
                        icon
                        labelPosition="left"
                        onClick={validateConfig}
                        loading={saving}
                      >
                        <Icon name="check circle" />
                        Validate
                      </Button>
                      <Button
                        positive
                        icon
                        labelPosition="left"
                        onClick={saveConfig}
                        loading={saving}
                        disabled={!hasChanges}
                      >
                        <Icon name="save" />
                        Save
                      </Button>
                      <Button
                        color="blue"
                        icon
                        labelPosition="left"
                        onClick={() =>
                          setConfirmModal({
                            open: true,
                            action: `Deploy ${selectedConfig}?`,
                            onConfirm: deployConfig,
                          })
                        }
                        disabled={hasChanges}
                      >
                        <Icon name="rocket" />
                        Deploy
                      </Button>
                      <Button
                        icon
                        labelPosition="left"
                        onClick={() => {
                          setConfigContent(originalContent);
                          setValidationResult(null);
                        }}
                        disabled={!hasChanges}
                      >
                        <Icon name="undo" />
                        Revert
                      </Button>
                    </div>
                    {validationResult && (
                      <Accordion styled fluid style={{ marginTop: "1em" }}>
                        <Accordion.Title active>
                          <Icon name="dropdown" />
                          Validation Results
                        </Accordion.Title>
                        <Accordion.Content active>
                          {validationResult.valid ? (
                            <Message positive>
                              <Icon name="check" /> Configuration is valid
                            </Message>
                          ) : (
                            <Message negative>
                              {validationResult.errors.map((error, idx) => (
                                <p key={idx}>
                                  <Icon name="times circle" />
                                  Line {error.line}: {error.message}
                                </p>
                              ))}
                            </Message>
                          )}
                          {validationResult.warnings.length > 0 && (
                            <Message warning>
                              {validationResult.warnings.map((warning, idx) => (
                                <p key={idx}>
                                  <Icon name="warning sign" />
                                  Line {warning.line}: {warning.message}
                                </p>
                              ))}
                            </Message>
                          )}
                        </Accordion.Content>
                      </Accordion>
                    )}
                  </>
                ) : (
                  <Message info>
                    <Icon name="info" />
                    Select a configuration file to edit
                  </Message>
                )}
              </Segment>
            </Grid.Column>
          </Grid>
        </Tab.Pane>
      ),
    },
    {
      menuItem: { key: "services", icon: "server", content: "Services" },
      render: () => (
        <Tab.Pane>
          <Table celled striped>
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell>Service</Table.HeaderCell>
                <Table.HeaderCell>Status</Table.HeaderCell>
                <Table.HeaderCell>Port</Table.HeaderCell>
                <Table.HeaderCell>Uptime</Table.HeaderCell>
                <Table.HeaderCell>Memory</Table.HeaderCell>
                <Table.HeaderCell>CPU</Table.HeaderCell>
                <Table.HeaderCell>Health</Table.HeaderCell>
                <Table.HeaderCell>Actions</Table.HeaderCell>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {services.map((service) => (
                <Table.Row key={service.name}>
                  <Table.Cell>
                    <Icon name="docker" />
                    {service.name}
                  </Table.Cell>
                  <Table.Cell>
                    <Label color={getStatusColor(service.status)}>
                      {service.status}
                    </Label>
                  </Table.Cell>
                  <Table.Cell>{service.port}</Table.Cell>
                  <Table.Cell>{service.uptime}</Table.Cell>
                  <Table.Cell>{service.memory}</Table.Cell>
                  <Table.Cell>{service.cpu}</Table.Cell>
                  <Table.Cell textAlign="center">
                    <Icon
                      name={
                        service.healthCheck ? "check circle" : "times circle"
                      }
                      color={service.healthCheck ? "green" : "red"}
                    />
                  </Table.Cell>
                  <Table.Cell>
                    <Dropdown icon="ellipsis vertical" direction="left">
                      <Dropdown.Menu>
                        <Dropdown.Item
                          icon="redo"
                          text="Restart"
                          onClick={() =>
                            setConfirmModal({
                              open: true,
                              action: `Restart ${service.name}?`,
                              onConfirm: () => restartService(service.name),
                            })
                          }
                        />
                        <Dropdown.Item icon="file alternate" text="View Logs" />
                        <Dropdown.Item icon="chart line" text="Metrics" />
                      </Dropdown.Menu>
                    </Dropdown>
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </Tab.Pane>
      ),
    },
    {
      menuItem: {
        key: "deployments",
        icon: "history",
        content: "Deployment History",
      },
      render: () => (
        <Tab.Pane>
          <Table celled striped>
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell>Timestamp</Table.HeaderCell>
                <Table.HeaderCell>File</Table.HeaderCell>
                <Table.HeaderCell>Action</Table.HeaderCell>
                <Table.HeaderCell>User</Table.HeaderCell>
                <Table.HeaderCell>Status</Table.HeaderCell>
                <Table.HeaderCell>Actions</Table.HeaderCell>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {deploymentHistory.map((deployment) => (
                <Table.Row key={deployment.id}>
                  <Table.Cell>
                    {new Date(deployment.timestamp).toLocaleString()}
                  </Table.Cell>
                  <Table.Cell>{deployment.file}</Table.Cell>
                  <Table.Cell>
                    <Label
                      color={deployment.action === "deploy" ? "blue" : "orange"}
                    >
                      {deployment.action}
                    </Label>
                  </Table.Cell>
                  <Table.Cell>{deployment.user}</Table.Cell>
                  <Table.Cell>
                    <Label
                      color={
                        deployment.status === "success"
                          ? "green"
                          : deployment.status === "failed"
                            ? "red"
                            : "yellow"
                      }
                    >
                      {deployment.status}
                    </Label>
                  </Table.Cell>
                  <Table.Cell>
                    {deployment.status === "success" &&
                      deployment.action === "deploy" && (
                        <Button
                          size="small"
                          color="orange"
                          onClick={() =>
                            setConfirmModal({
                              open: true,
                              action: `Rollback to deployment ${deployment.id}?`,
                              onConfirm: () => rollbackConfig(deployment.id),
                            })
                          }
                        >
                          <Icon name="undo" /> Rollback
                        </Button>
                      )}
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </Tab.Pane>
      ),
    },
  ];

  // ============================================================================
  // Main Render
  // ============================================================================

  return (
    <Container fluid style={{ padding: "2em" }}>
      <Dimmer active={loading} inverted>
        <Loader>Loading...</Loader>
      </Dimmer>

      <Header as="h1" dividing>
        <Icon name="cogs" />
        <Header.Content>
          Admin Portal
          <Header.Subheader>
            Configuration Management & Service Monitoring
          </Header.Subheader>
        </Header.Content>
      </Header>

      {message && (
        <Message
          positive={message.type === "success"}
          negative={message.type === "error"}
          warning={message.type === "warning"}
          onDismiss={() => setMessage(null)}
        >
          {message.text}
        </Message>
      )}

      <Tab
        panes={panes}
        activeIndex={activeTab}
        onTabChange={(_, data) => setActiveTab(data.activeIndex as number)}
      />

      <Modal
        size="tiny"
        open={confirmModal.open}
        onClose={() =>
          setConfirmModal({ open: false, action: "", onConfirm: () => {} })
        }
      >
        <Modal.Header>Confirm Action</Modal.Header>
        <Modal.Content>
          <p>{confirmModal.action}</p>
        </Modal.Content>
        <Modal.Actions>
          <Button
            negative
            onClick={() =>
              setConfirmModal({ open: false, action: "", onConfirm: () => {} })
            }
          >
            Cancel
          </Button>
          <Button positive onClick={confirmModal.onConfirm} loading={saving}>
            Confirm
          </Button>
        </Modal.Actions>
      </Modal>
    </Container>
  );
};

export default AdminPortal;
