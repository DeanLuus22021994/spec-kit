import axios, { AxiosError } from "axios";
import React, { useCallback, useEffect, useState } from "react";
import {
  Button,
  Card,
  Container,
  Dimmer,
  Dropdown,
  Grid,
  Header,
  Icon,
  Label,
  Loader,
  Menu,
  Message,
  Progress,
  Segment,
  Statistic,
  Table,
} from "semantic-ui-react";

// ============================================================================
// Types
// ============================================================================

interface MetricValue {
  current: number;
  change: number;
  changePercent: number;
  trend: "up" | "down" | "stable";
}

interface OverviewMetrics {
  totalRequests: MetricValue;
  activeAgents: MetricValue;
  avgResponseTime: MetricValue;
  gpuUtilization: MetricValue;
  memoryUsage: MetricValue;
  errorRate: MetricValue;
}

interface AgentSession {
  sessionId: string;
  agentType: string;
  startTime: string;
  duration: string;
  status: "active" | "completed" | "error";
  tokensUsed: number;
  decisionsCount: number;
}

interface CostData {
  dailyCost: number;
  monthlyProjection: number;
  costByService: ServiceCost[];
  costTrend: CostTrendPoint[];
  topCostDrivers: CostDriver[];
}

interface ServiceCost {
  service: string;
  cost: number;
  percentage: number;
}

interface CostTrendPoint {
  date: string;
  cost: number;
}

interface CostDriver {
  operation: string;
  count: number;
  avgCost: number;
  totalCost: number;
}

interface PerformanceData {
  latencyP50: number;
  latencyP95: number;
  latencyP99: number;
  throughput: number;
  errorRate: number;
  gpuMemory: {
    used: number;
    total: number;
    percentage: number;
  };
}

interface ApiError {
  message?: string;
  error?: string;
}

type TimeRange = "1h" | "6h" | "24h" | "7d" | "30d";

// ============================================================================
// Dashboard Component
// ============================================================================

const Dashboard: React.FC = () => {
  // State
  const [activeView, setActiveView] = useState<
    "overview" | "agents" | "costs" | "performance"
  >("overview");
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const [overview, setOverview] = useState<OverviewMetrics | null>(null);
  const [agentSessions, setAgentSessions] = useState<AgentSession[]>([]);
  const [costData, setCostData] = useState<CostData | null>(null);
  const [performanceData, setPerformanceData] =
    useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // ============================================================================
  // API Functions
  // ============================================================================

  const fetchOverview = useCallback(async () => {
    try {
      const response = await axios.get<OverviewMetrics>(
        `/api/dashboard/overview?range=${timeRange}`,
      );
      setOverview(response.data);
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      setError(
        axiosError.response?.data?.message ??
          "Failed to fetch overview metrics",
      );
    }
  }, [timeRange]);

  const fetchAgentSessions = useCallback(async () => {
    try {
      const response = await axios.get<AgentSession[]>(
        `/api/dashboard/agents?range=${timeRange}`,
      );
      setAgentSessions(response.data);
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      setError(
        axiosError.response?.data?.message ?? "Failed to fetch agent sessions",
      );
    }
  }, [timeRange]);

  const fetchCostData = useCallback(async () => {
    try {
      const response = await axios.get<CostData>(
        `/api/dashboard/costs?range=${timeRange}`,
      );
      setCostData(response.data);
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      setError(
        axiosError.response?.data?.message ?? "Failed to fetch cost data",
      );
    }
  }, [timeRange]);

  const fetchPerformanceData = useCallback(async () => {
    try {
      const response = await axios.get<PerformanceData>(
        `/api/dashboard/performance?range=${timeRange}`,
      );
      setPerformanceData(response.data);
    } catch (err) {
      const axiosError = err as AxiosError<ApiError>;
      setError(
        axiosError.response?.data?.message ??
          "Failed to fetch performance data",
      );
    }
  }, [timeRange]);

  const fetchAllData = useCallback(async () => {
    setLoading(true);
    setError(null);
    await Promise.all([
      fetchOverview(),
      fetchAgentSessions(),
      fetchCostData(),
      fetchPerformanceData(),
    ]);
    setLoading(false);
  }, [fetchOverview, fetchAgentSessions, fetchCostData, fetchPerformanceData]);

  useEffect(() => {
    void fetchAllData();

    // Real-time updates every 5 seconds
    const interval = setInterval(() => {
      void fetchAllData();
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchAllData]);

  // ============================================================================
  // Render Helpers
  // ============================================================================

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toFixed(0);
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(amount);
  };

  const formatDuration = (ms: number): string => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const getTrendIcon = (trend: "up" | "down" | "stable"): JSX.Element => {
    switch (trend) {
      case "up":
        return <Icon name="arrow up" color="green" />;
      case "down":
        return <Icon name="arrow down" color="red" />;
      default:
        return <Icon name="minus" color="grey" />;
    }
  };

  // ============================================================================
  // View Components
  // ============================================================================

  const renderOverview = () => (
    <Grid>
      <Grid.Row columns={3}>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Statistic size="small">
                <Statistic.Value>
                  {overview
                    ? formatNumber(overview.totalRequests.current)
                    : "-"}
                </Statistic.Value>
                <Statistic.Label>Total Requests</Statistic.Label>
              </Statistic>
              {overview && (
                <div className="dashboard-trend-container">
                  {getTrendIcon(overview.totalRequests.trend)}
                  <span
                    className={
                      overview.totalRequests.change >= 0
                        ? "dashboard-trend-positive"
                        : "dashboard-trend-negative"
                    }
                  >
                    {overview.totalRequests.changePercent.toFixed(1)}%
                  </span>
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Statistic size="small" color="blue">
                <Statistic.Value>
                  {overview ? overview.activeAgents.current : "-"}
                </Statistic.Value>
                <Statistic.Label>Active Agents</Statistic.Label>
              </Statistic>
            </Card.Content>
          </Card>
        </Grid.Column>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Statistic size="small" color="teal">
                <Statistic.Value>
                  {overview
                    ? formatDuration(overview.avgResponseTime.current)
                    : "-"}
                </Statistic.Value>
                <Statistic.Label>Avg Response Time</Statistic.Label>
              </Statistic>
            </Card.Content>
          </Card>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row columns={3}>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Header as="h4">GPU Utilization</Header>
              <Progress
                percent={overview?.gpuUtilization.current ?? 0}
                color={
                  (overview?.gpuUtilization.current ?? 0) > 90
                    ? "red"
                    : (overview?.gpuUtilization.current ?? 0) > 70
                      ? "yellow"
                      : "green"
                }
                progress
              />
            </Card.Content>
          </Card>
        </Grid.Column>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Header as="h4">Memory Usage</Header>
              <Progress
                percent={overview?.memoryUsage.current ?? 0}
                color={
                  (overview?.memoryUsage.current ?? 0) > 90
                    ? "red"
                    : (overview?.memoryUsage.current ?? 0) > 70
                      ? "yellow"
                      : "green"
                }
                progress
              />
            </Card.Content>
          </Card>
        </Grid.Column>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Header as="h4">Error Rate</Header>
              <Statistic
                size="mini"
                color={(overview?.errorRate.current ?? 0) > 5 ? "red" : "green"}
              >
                <Statistic.Value>
                  {overview?.errorRate.current.toFixed(2) ?? "0"}%
                </Statistic.Value>
              </Statistic>
            </Card.Content>
          </Card>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );

  const renderAgents = () => (
    <Segment>
      <Header as="h3">
        <Icon name="microchip" />
        Agent Sessions
      </Header>
      <Table celled striped>
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell>Session ID</Table.HeaderCell>
            <Table.HeaderCell>Agent Type</Table.HeaderCell>
            <Table.HeaderCell>Start Time</Table.HeaderCell>
            <Table.HeaderCell>Duration</Table.HeaderCell>
            <Table.HeaderCell>Status</Table.HeaderCell>
            <Table.HeaderCell>Tokens Used</Table.HeaderCell>
            <Table.HeaderCell>Decisions</Table.HeaderCell>
            <Table.HeaderCell>Actions</Table.HeaderCell>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {agentSessions.map((session) => (
            <Table.Row key={session.sessionId}>
              <Table.Cell>
                <code>{session.sessionId.substring(0, 8)}...</code>
              </Table.Cell>
              <Table.Cell>
                <Label color="blue">{session.agentType}</Label>
              </Table.Cell>
              <Table.Cell>
                {new Date(session.startTime).toLocaleString()}
              </Table.Cell>
              <Table.Cell>{session.duration}</Table.Cell>
              <Table.Cell>
                <Label
                  color={
                    session.status === "active"
                      ? "green"
                      : session.status === "completed"
                        ? "blue"
                        : "red"
                  }
                >
                  {session.status}
                </Label>
              </Table.Cell>
              <Table.Cell>{formatNumber(session.tokensUsed)}</Table.Cell>
              <Table.Cell>{session.decisionsCount}</Table.Cell>
              <Table.Cell>
                <Button icon size="small" color="teal" title="View Trace">
                  <Icon name="search" />
                </Button>
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table>
    </Segment>
  );

  const renderCosts = () => (
    <Grid>
      <Grid.Row columns={2}>
        <Grid.Column>
          <Card fluid color="green">
            <Card.Content>
              <Card.Header>Daily Cost</Card.Header>
              <Statistic size="small" color="green">
                <Statistic.Value>
                  {costData ? formatCurrency(costData.dailyCost) : "-"}
                </Statistic.Value>
              </Statistic>
            </Card.Content>
          </Card>
        </Grid.Column>
        <Grid.Column>
          <Card fluid color="blue">
            <Card.Content>
              <Card.Header>Monthly Projection</Card.Header>
              <Statistic size="small" color="blue">
                <Statistic.Value>
                  {costData ? formatCurrency(costData.monthlyProjection) : "-"}
                </Statistic.Value>
              </Statistic>
            </Card.Content>
          </Card>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column width={8}>
          <Segment>
            <Header as="h4">Cost by Service</Header>
            {costData?.costByService.map((service) => (
              <div key={service.service} className="dashboard-service-item">
                <div className="dashboard-service-header">
                  <span>{service.service}</span>
                  <span>{formatCurrency(service.cost)}</span>
                </div>
                <Progress
                  percent={service.percentage}
                  size="small"
                  color="blue"
                />
              </div>
            ))}
          </Segment>
        </Grid.Column>
        <Grid.Column width={8}>
          <Segment>
            <Header as="h4">Top Cost Drivers</Header>
            <Table compact size="small">
              <Table.Header>
                <Table.Row>
                  <Table.HeaderCell>Operation</Table.HeaderCell>
                  <Table.HeaderCell>Count</Table.HeaderCell>
                  <Table.HeaderCell>Avg Cost</Table.HeaderCell>
                  <Table.HeaderCell>Total</Table.HeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {costData?.topCostDrivers.map((driver) => (
                  <Table.Row key={driver.operation}>
                    <Table.Cell>{driver.operation}</Table.Cell>
                    <Table.Cell>{formatNumber(driver.count)}</Table.Cell>
                    <Table.Cell>{formatCurrency(driver.avgCost)}</Table.Cell>
                    <Table.Cell>{formatCurrency(driver.totalCost)}</Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </Segment>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );

  const renderPerformance = () => (
    <Grid>
      <Grid.Row columns={4}>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Card.Header>Latency P50</Card.Header>
              <Statistic size="tiny">
                <Statistic.Value>
                  {performanceData
                    ? formatDuration(performanceData.latencyP50)
                    : "-"}
                </Statistic.Value>
              </Statistic>
            </Card.Content>
          </Card>
        </Grid.Column>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Card.Header>Latency P95</Card.Header>
              <Statistic size="tiny">
                <Statistic.Value>
                  {performanceData
                    ? formatDuration(performanceData.latencyP95)
                    : "-"}
                </Statistic.Value>
              </Statistic>
            </Card.Content>
          </Card>
        </Grid.Column>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Card.Header>Latency P99</Card.Header>
              <Statistic size="tiny">
                <Statistic.Value>
                  {performanceData
                    ? formatDuration(performanceData.latencyP99)
                    : "-"}
                </Statistic.Value>
              </Statistic>
            </Card.Content>
          </Card>
        </Grid.Column>
        <Grid.Column>
          <Card fluid>
            <Card.Content>
              <Card.Header>Throughput</Card.Header>
              <Statistic size="tiny">
                <Statistic.Value>
                  {performanceData
                    ? `${formatNumber(performanceData.throughput)}/s`
                    : "-"}
                </Statistic.Value>
              </Statistic>
            </Card.Content>
          </Card>
        </Grid.Column>
      </Grid.Row>
      <Grid.Row>
        <Grid.Column width={8}>
          <Segment>
            <Header as="h4">GPU Memory</Header>
            <Progress
              value={performanceData?.gpuMemory.used ?? 0}
              total={performanceData?.gpuMemory.total ?? 100}
              progress="ratio"
              color={
                (performanceData?.gpuMemory.percentage ?? 0) > 90
                  ? "red"
                  : (performanceData?.gpuMemory.percentage ?? 0) > 70
                    ? "yellow"
                    : "green"
              }
            />
            <p className="dashboard-gpu-memory">
              {performanceData
                ? `${(performanceData.gpuMemory.used / 1024).toFixed(1)} GB / ${(
                    performanceData.gpuMemory.total / 1024
                  ).toFixed(1)} GB`
                : "-"}
            </p>
          </Segment>
        </Grid.Column>
        <Grid.Column width={8}>
          <Segment>
            <Header as="h4">Error Rate</Header>
            <Statistic
              size="small"
              color={(performanceData?.errorRate ?? 0) > 5 ? "red" : "green"}
            >
              <Statistic.Value>
                {performanceData?.errorRate.toFixed(2) ?? "0"}%
              </Statistic.Value>
            </Statistic>
          </Segment>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );

  // ============================================================================
  // Main Render
  // ============================================================================

  const viewOptions = [
    { key: "overview", text: "Overview", value: "overview", icon: "dashboard" },
    { key: "agents", text: "Agents", value: "agents", icon: "robot" },
    { key: "costs", text: "Costs", value: "costs", icon: "dollar" },
    {
      key: "performance",
      text: "Performance",
      value: "performance",
      icon: "chart line",
    },
  ];

  const timeRangeOptions = [
    { key: "1h", text: "Last Hour", value: "1h" },
    { key: "6h", text: "Last 6 Hours", value: "6h" },
    { key: "24h", text: "Last 24 Hours", value: "24h" },
    { key: "7d", text: "Last 7 Days", value: "7d" },
    { key: "30d", text: "Last 30 Days", value: "30d" },
  ];

  return (
    <Container fluid style={{ padding: "2em" }}>
      <Dimmer active={loading} inverted>
        <Loader>Loading Dashboard...</Loader>
      </Dimmer>

      <Menu secondary>
        <Menu.Item>
          <Header as="h1">
            <Icon name="chart bar" />
            <Header.Content>
              Dashboard
              <Header.Subheader>
                Real-time metrics and analytics
              </Header.Subheader>
            </Header.Content>
          </Header>
        </Menu.Item>
        <Menu.Menu position="right">
          <Menu.Item>
            <Dropdown
              selection
              options={viewOptions}
              value={activeView}
              onChange={(_, data) =>
                setActiveView(data.value as typeof activeView)
              }
            />
          </Menu.Item>
          <Menu.Item>
            <Dropdown
              selection
              options={timeRangeOptions}
              value={timeRange}
              onChange={(_, data) => setTimeRange(data.value as TimeRange)}
            />
          </Menu.Item>
          <Menu.Item>
            <Button icon onClick={() => void fetchAllData()}>
              <Icon name="refresh" />
            </Button>
          </Menu.Item>
        </Menu.Menu>
      </Menu>

      {error && (
        <Message negative onDismiss={() => setError(null)}>
          <Message.Header>Error</Message.Header>
          <p>{error}</p>
        </Message>
      )}

      <Segment>
        {activeView === "overview" && renderOverview()}
        {activeView === "agents" && renderAgents()}
        {activeView === "costs" && renderCosts()}
        {activeView === "performance" && renderPerformance()}
      </Segment>
    </Container>
  );
};

export default Dashboard;
