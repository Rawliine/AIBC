# One-Command Startup System Documentation

## Overview

The One-Command Startup System provides a streamlined developer experience for the AIBC (AI & Blockchain) project. Instead of manually starting multiple services in the correct order, developers can now use a single command to bring up the entire development environment.

## Architecture

### Components

The startup system consists of four main components:

1. **Environment Configuration** (`env.example`)
2. **Build System** (`Makefile`)
3. **Startup Script** (`scripts/dev_up.sh`)
4. **Shutdown Script** (`scripts/dev_down.sh`)

### System Flow

```
make dev-up
    ↓
Makefile calls scripts/dev_up.sh
    ↓
dev_up.sh performs:
    1. Dependency checks
    2. IPFS initialization & startup
    3. Hardhat node startup
    4. Contract compilation
    5. Contract deployment
    6. Health checks
    7. Status reporting
```

## File Structure

```
AIBC/
├── env.example                 # Environment configuration template
├── Makefile                   # Build system and command interface
├── scripts/
│   ├── dev_up.sh             # Startup orchestration script
│   └── dev_down.sh           # Shutdown script
├── logs/                     # Service logs (created automatically)
│   ├── ipfs.log             # IPFS daemon output
│   └── hardhat.log          # Hardhat node output
└── docs/
    └── OneCommandStartup.md  # This documentation
```

## Detailed Component Documentation

### 1. Environment Configuration (`env.example`)

**Purpose**: Provides a clean template for all required environment variables.

**Key Sections**:
- **Blockchain Configuration**: RPC URL, Chain ID, Network name
- **Private Keys**: Hardhat default accounts for local development
- **IPFS Configuration**: API endpoint
- **Logging Configuration**: Log levels, directories, formats
- **Environment Profile**: Development vs test mode
- **Ray Configuration**: Distributed computing settings
- **Production Settings**: Testnet/mainnet configurations (commented)

**Security Features**:
- No actual secrets included (template only)
- Clear separation of local vs production settings
- Hardhat default keys safe for local development

**Usage**:
```bash
cp env.example .env
# Edit .env with your specific values if needed
```

### 2. Build System (`Makefile`)

**Purpose**: Provides a unified interface for all development operations.

#### Available Targets

| Command | Description | Dependencies |
|---------|-------------|--------------|
| `help` | Show available commands | None |
| `setup` | Install Python + Node.js dependencies | pip, npm |
| `dev-up` | Start complete development environment | .env file |
| `dev-down` | Stop all services and cleanup | None |
| `dev-status` | Check service health | curl |
| `trainer` | Run D-PoDL trainer | Running services |
| `logs-ipfs` | Tail IPFS logs | IPFS running |
| `logs-hardhat` | Tail Hardhat logs | Hardhat running |
| `logs-all` | Tail all service logs | Services running |
| `test` | Run all tests | Dependencies installed |
| `test-e2e` | Run end-to-end tests | Running services |
| `clean` | Clean logs and temp files | None |

#### Design Principles

1. **Fail Fast**: Check prerequisites before proceeding
2. **Clear Output**: Colored, structured feedback
3. **Safety**: Verify .env exists before starting services
4. **Flexibility**: Individual commands for granular control

### 3. Startup Script (`scripts/dev_up.sh`)

**Purpose**: Orchestrates the complete startup sequence with health checks.

#### Key Features

##### Dependency Validation
```bash
check_dependency() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed or not in PATH"
        exit 1
    fi
}
```

Validates that required tools are available:
- `ipfs` - IPFS daemon
- `node` - Node.js runtime
- `npx` - Node package executor
- `curl` - HTTP client for health checks

##### Service Health Checks
```bash
wait_for_service() {
    local url=$1
    local service_name=$2
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s $url > /dev/null 2>&1; then
            return 0
        fi
        sleep $RETRY_DELAY
        retries=$((retries + 1))
    done
    
    return 1
}
```

- **Configurable Timeouts**: 30 retries with 1-second delays
- **Progress Reporting**: Status updates every 10 retries
- **Multiple Endpoints**: IPFS API and Hardhat RPC
- **Graceful Failure**: Clear error messages on timeout

##### Background Process Management

**IPFS Daemon**:
```bash
nohup ipfs daemon > $IPFS_LOG 2>&1 & disown
```

**Hardhat Node**:
```bash
nohup npx hardhat node > ../$HARDHAT_LOG 2>&1 & disown
```

- **`nohup`**: Prevents termination when parent shell closes
- **`disown`**: Removes from shell job control
- **Logging**: All output captured to log files
- **Error Handling**: Both stdout and stderr redirected

##### Smart Service Detection

The script checks if services are already running before starting new instances:

```bash
if pgrep -f "ipfs daemon" > /dev/null; then
    print_warning "IPFS daemon is already running"
else
    # Start new instance
fi
```

This prevents conflicts and allows idempotent execution.

##### IPFS Initialization

Automatically initializes IPFS repository if it doesn't exist:

```bash
if [ ! -d ~/.ipfs ]; then
    print_status "Initializing IPFS..."
    ipfs init
fi
```

#### Error Handling

1. **Signal Handling**: Traps SIGINT/SIGTERM for cleanup
2. **Exit Codes**: Proper error codes for automation
3. **Rollback**: Calls cleanup script on failure
4. **Validation**: Checks each step before proceeding

#### Status Reporting

The script provides comprehensive status information:
- Service URLs and ports
- Log file locations
- Next steps for the developer
- Visual indicators (✅ success, ❌ error, ⚠️ warning)

### 4. Shutdown Script (`scripts/dev_down.sh`)

**Purpose**: Cleanly stops all services and performs cleanup.

#### Graceful Shutdown Process

```bash
stop_service() {
    local service_name=$1
    local process_pattern=$2
    
    # 1. Find running processes
    local pids=$(pgrep -f "$process_pattern" || true)
    
    # 2. Send SIGTERM (graceful)
    for pid in $pids; do
        kill -TERM $pid 2>/dev/null
    done
    
    # 3. Wait for graceful shutdown
    sleep 3
    
    # 4. Force kill if necessary
    local remaining_pids=$(pgrep -f "$process_pattern" || true)
    if [ -n "$remaining_pids" ]; then
        for pid in $remaining_pids; do
            kill -KILL $pid 2>/dev/null || true
        done
    fi
    
    # 5. Verify shutdown
    # ...
}
```

#### Service Shutdown Order

1. **Hardhat Node**: Stops blockchain simulation
2. **IPFS Daemon**: Stops distributed storage
3. **Ray Processes**: Cleans up any distributed computing processes

#### Log Preservation

By default, log files are preserved for debugging:
- Logs remain in `logs/` directory
- Use `make clean` to remove old logs
- Developers can review issues after shutdown

## Usage Guide

### First-Time Setup

```bash
# 1. Clone repository and navigate to project
git clone <repository-url>
cd AIBC

# 2. Copy environment template
cp env.example .env

# 3. Install dependencies
make setup

# 4. Start development environment
make dev-up
```

### Daily Development Workflow

```bash
# Start working
make dev-up

# Check if everything is running
make dev-status

# Run the trainer
make trainer

# Follow logs (in another terminal)
make logs-all

# Run tests
make test

# Stop when done
make dev-down
```

### Advanced Usage

#### Custom Environment Variables

Edit `.env` file to customize:

```bash
# Use full dataset instead of test dataset
DPODL_ENV="dev"

# Increase logging verbosity
LOG_LEVEL="DEBUG"

# Use remote Ray cluster
RAY_ADDRESS="ray://remote-head:10001"
```

#### Selective Service Management

Start individual services:

```bash
# Just start Hardhat (foreground)
make chain

# Just deploy contracts
make deploy

# Just run trainer
make trainer
```

#### Log Management

```bash
# Follow specific service logs
make logs-ipfs
make logs-hardhat

# Clean old logs
make clean
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Symptoms**:
```
Error: listen EADDRINUSE: address already in use :::8545
```

**Solutions**:
```bash
# Check what's using the port
lsof -i :8545

# Kill the process
kill <PID>

# Or use dev-down to clean up
make dev-down
```

#### 2. IPFS Initialization Fails

**Symptoms**:
```
Error: ipfs configuration file already exists!
```

**Solutions**:
```bash
# This is normal - IPFS is already initialized
# The script handles this automatically
```

#### 3. Services Don't Start

**Symptoms**:
```
❌ Hardhat RPC not responsive
```

**Solutions**:
```bash
# Check logs for errors
make logs-hardhat

# Verify dependencies
which node npx ipfs

# Check disk space
df -h

# Try manual startup for debugging
cd blockchain
npx hardhat node
```

#### 4. Permission Denied on Scripts

**Symptoms**:
```
Permission denied: ./scripts/dev_up.sh
```

**Solutions**:
```bash
# Fix permissions
chmod +x scripts/*.sh

# Or reinstall
make setup
```

### Health Check Failures

If health checks consistently fail:

1. **Check Network Connectivity**:
   ```bash
   curl http://127.0.0.1:8545
   curl http://127.0.0.1:5001/api/v0/version
   ```

2. **Verify Process Status**:
   ```bash
   ps aux | grep -E "(ipfs|hardhat)"
   ```

3. **Check Log Files**:
   ```bash
   tail -f logs/ipfs.log
   tail -f logs/hardhat.log
   ```

4. **Manual Service Start**:
   ```bash
   # Start IPFS manually
   ipfs daemon
   
   # Start Hardhat manually
   cd blockchain && npx hardhat node
   ```

### Performance Issues

#### Slow Startup

If startup takes longer than expected:

1. **Check System Resources**:
   ```bash
   top
   df -h
   ```

2. **Reduce Timeouts** (for faster feedback):
   Edit `scripts/dev_up.sh`:
   ```bash
   MAX_RETRIES=10  # Reduce from 30
   ```

3. **Skip Health Checks** (debugging only):
   Comment out `wait_for_service` calls in `dev_up.sh`

#### High Resource Usage

Monitor resource usage:

```bash
# CPU and memory
htop

# Disk I/O
iotop

# Network
netstat -tulpn
```

## Customization Guide

### Adding New Services

To add a new service to the startup sequence:

1. **Update `dev_up.sh`**:
   ```bash
   # Add after existing services
   print_status "Starting MyService..."
   nohup my-service > $LOGS_DIR/myservice.log 2>&1 & disown
   
   if ! wait_for_service "http://127.0.0.1:3000" "MyService"; then
       print_error "Failed to start MyService"
       exit 1
   fi
   ```

2. **Update `dev_down.sh`**:
   ```bash
   # Add to shutdown sequence
   stop_service "MyService" "my-service"
   ```

3. **Update `Makefile`**:
   ```bash
   logs-myservice:
   	@tail -f $(LOGS_DIR)/myservice.log
   ```

### Custom Health Checks

Add application-specific health checks:

```bash
check_contract_deployment() {
    local retries=0
    while [ $retries -lt 10 ]; do
        if curl -s -X POST \
            -H "Content-Type: application/json" \
            -d '{"jsonrpc":"2.0","method":"eth_getCode","params":["0x5FbDB2315678afecb367f032d93F642f64180aa3","latest"],"id":1}' \
            http://127.0.0.1:8545 | grep -q '"result":"0x'; then
            return 0
        fi
        sleep 1
        retries=$((retries + 1))
    done
    return 1
}
```

### Environment-Specific Configurations

Create environment-specific startup scripts:

```bash
# scripts/dev_up_production.sh
# Production-specific startup logic

# scripts/dev_up_testing.sh  
# Testing-specific startup logic
```

Update Makefile:
```makefile
dev-up-prod:
	@scripts/dev_up_production.sh

dev-up-test:
	@scripts/dev_up_testing.sh
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup environment
        run: |
          cp env.example .env
          make setup
          
      - name: Start services
        run: make dev-up
        
      - name: Run tests
        run: make test
        
      - name: Cleanup
        run: make dev-down
```

### Docker Integration

Create a Docker Compose override:

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  dev-env:
    build: .
    volumes:
      - .:/workspace
    working_dir: /workspace
    command: make dev-up
    ports:
      - "8545:8545"
      - "5001:5001"
```

## Security Considerations

### Local Development Safety

1. **Default Keys**: Uses Hardhat's well-known test keys
2. **Local Networks**: Only binds to localhost by default
3. **No Real Funds**: Test tokens only

### Production Deployment

**Do NOT use this system for production**:
- Private keys are stored in plain text
- No encryption or secrets management
- Services bind to all interfaces
- No authentication or authorization

For production, use:
- Kubernetes or Docker Swarm
- Secrets management (Vault, AWS Secrets Manager)
- Proper networking and firewalls
- Certificate management

## Monitoring and Observability

### Log Aggregation

Integrate with log aggregation systems:

```bash
# Filebeat configuration for ELK stack
filebeat.inputs:
- type: log
  paths:
    - /path/to/AIBC/logs/*.log
  fields:
    service: aibc-dev
    environment: development
```

### Metrics Collection

Add Prometheus metrics:

```bash
# Add to dev_up.sh
print_status "Starting metrics collection..."
prometheus --config.file=prometheus.yml &
```

### Health Check Endpoints

Expose health check endpoints:

```bash
# Add health check route
curl http://127.0.0.1:8545/health
curl http://127.0.0.1:5001/api/v0/id
```

## Future Enhancements

### Planned Features

1. **Configuration Validation**: Validate .env file format
2. **Service Dependencies**: Smart dependency ordering
3. **Resource Monitoring**: CPU/memory usage tracking
4. **Auto-restart**: Restart failed services
5. **Multi-environment**: Support for multiple environments
6. **Database Integration**: Add database startup/migration
7. **Load Balancing**: Multiple service instances

### Extension Points

The system is designed for extensibility:

- **Plugin Architecture**: Add service plugins
- **Custom Hooks**: Pre/post startup hooks
- **Configuration Templates**: Multiple .env templates
- **Service Discovery**: Automatic service registration

## Conclusion

The One-Command Startup System significantly reduces the complexity of local development for the AIBC project. By automating the orchestration of multiple services, providing robust health checks, and offering comprehensive monitoring, it enables developers to focus on building features rather than managing infrastructure.

The system balances simplicity with flexibility, providing sensible defaults while allowing for extensive customization. Its modular design ensures that it can evolve with the project's needs while maintaining backward compatibility.

For questions or issues, refer to the troubleshooting section or consult the main project documentation.
