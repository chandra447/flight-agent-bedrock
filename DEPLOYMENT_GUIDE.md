# Multi-Agent Bedrock System Deployment Guide

## 🎯 What We've Built

A comprehensive multi-agent Bedrock system with:

### **2 Bedrock Agents**
1. **Network Specialist Agent** - Handles network connectivity, proxy configuration, and network rule validation
2. **Supervisor Agent** - Coordinates requests and collaborates with specialist agents (configured with `agent_collaboration = "SUPERVISOR"`)

### **2 Lambda Functions**
1. **Network Specialist Lambda** (`network_specialist.py`) - Provides network analysis capabilities
2. **Supervisor Lambda** (`supervisor.py`) - Handles coordination and decision-making

### **Complete Infrastructure**
- IAM roles and policies for both agents and Lambda functions
- Agent aliases for production deployment
- Agent collaboration setup (Supervisor → Network Specialist)
- Proper permissions and security configurations

## 🔧 Required GitHub Repository Secrets

Set up these secrets in your GitHub repository:

### **Required Secrets (OIDC Authentication)**
```
TF_STATE_BUCKET           # S3 bucket for Terraform state (e.g., "my-terraform-state-bucket")
```

**Note**: We're using OIDC (OpenID Connect) authentication with the IAM role `arn:aws:iam::095811638868:role/git-action-tf`, so no AWS access keys are needed! 🔒

### **IAM Role Configuration**
Your IAM role `git-action-tf` already has the required permissions for:
- Bedrock (all operations)
- IAM (create/manage roles and policies)
- Lambda (create/manage functions)
- S3 (state bucket access)
- CloudWatch Logs

## 🚀 Deployment Options

### **Option 1: Production Deployment (Main Branch)**
```bash
git push origin main
```
- Automatically deploys to production
- Creates stack: `bedrock-multi-agent-prod`

### **Option 2: Feature Branch - Format Check Only**
```bash
git checkout -b feature/add-iam-role
# Make changes
git commit -m "Add new IAM role configuration"
git push origin feature/add-iam-role
```
- Only runs `terraform fmt --recursive`
- No deployment happens

### **Option 3: Feature Branch - Create Isolated Environment**
```bash
git checkout -b feature/add-iam-role
# Make changes
git commit -m "Add new feature - terraform deploy"
git push origin feature/add-iam-role
```
- Include `terraform deploy` in commit message
- Creates isolated test stack: `bedrock-multi-agent-test-{8-char-commit-hash}`
- Uses commit hash as prefix for unique naming

### **Option 4: Feature Branch - Destroy Isolated Environment**
```bash
# On the same branch where you created the environment
git commit -m "Clean up test environment - terraform destroy"
git push origin feature/add-iam-role
```
- Include `terraform destroy` in commit message
- Destroys the isolated environment created by the same commit hash
- Removes state file from S3

### **Option 5: Manual Local Deployment**
```bash
# Set variables
export TF_VAR_foundation_model="mistral.mistral-7b-instruct-v0:2"
export TF_VAR_environment="dev"
export TF_VAR_project_name="bedrock-multi-agent-dev"
export TF_VAR_aws_region="ap-southeast-2"

# Deploy
terraform init
terraform plan
terraform apply
```

## 🎛️ Configuration Variables

The system uses these configurable variables:

```hcl
# Foundation model (configurable)
foundation_model = "mistral.mistral-7b-instruct-v0:2"

# Environment
environment = "dev" | "test" | "production"

# Project naming
project_name = "bedrock-multi-agent"

# AWS region
aws_region = "ap-southeast-2"
```

## 📁 Project Structure

```
bedrock-agents/
├── main.tf                           # Main infrastructure
├── modules/auto-agents/              # Reusable Bedrock agent module
│   ├── main.tf                      # Agent resources
│   ├── variables.tf                 # Input variables
│   ├── outputs.tf                   # Outputs
│   ├── iam.tf                       # IAM roles and policies
│   ├── actiongroups.tf              # Action group resources
│   └── collaborators.tf             # Agent collaborator resources
├── lambda_functions/                 # Lambda source code
│   ├── network_specialist.py        # Network specialist logic
│   └── supervisor.py                # Supervisor coordination logic
├── agent_instructions/               # Agent instruction files
│   ├── network_specialist_instruction.txt
│   └── supervisor_instruction.txt
├── .github/workflows/               # CI/CD workflows
│   ├── terraform-deploy.yml         # Main deployment workflow
│   └── cleanup-branch.yml           # Branch cleanup workflow
├── docs/                            # Documentation
│   └── SETUP.md                     # Detailed setup guide
└── examples/                        # Usage examples
    ├── supervisor-agent/
    ├── supervisor-with-collaborators/
    └── complete/
```

## 🔄 How the Multi-Agent System Works

### **Request Flow**
1. **User** → **Supervisor Agent**
2. **Supervisor Agent** analyzes request using `analyze_request` function
3. **Supervisor Agent** coordinates with **Network Specialist** using `coordinate_specialists`
4. **Network Specialist** performs technical analysis using its specialized functions
5. **Supervisor Agent** consolidates responses using `consolidate_response`
6. **Supervisor Agent** provides final recommendation to user

### **Agent Capabilities**

**Network Specialist Agent:**
- `check_connectivity` - Test network connectivity
- `analyze_proxy_config` - Analyze proxy requirements
- `validate_network_rules` - Validate network configurations

**Supervisor Agent:**
- `analyze_request` - Analyze and triage requests
- `coordinate_specialists` - Coordinate with specialist agents
- `consolidate_response` - Synthesize specialist recommendations

## 🎯 Testing the System

After deployment, you can test the agents through:

1. **AWS Bedrock Console** - Test individual agents
2. **AWS CLI** - Invoke agents programmatically
3. **SDK Integration** - Integrate into applications

### **Example Test Commands**
```bash
# Test Network Specialist
aws bedrock-agent-runtime invoke-agent \
  --agent-id <network-specialist-agent-id> \
  --agent-alias-id <alias-id> \
  --session-id test-session \
  --input-text "Check connectivity to google.com"

# Test Supervisor (will coordinate with Network Specialist)
aws bedrock-agent-runtime invoke-agent \
  --agent-id <supervisor-agent-id> \
  --agent-alias-id <alias-id> \
  --session-id test-session \
  --input-text "I need to configure proxy access for api.example.com"
```

## 🔧 Customization Options

### **Change Foundation Model**
Update the `foundation_model` variable or GitHub Actions environment variable:
```yaml
env:
  TF_VAR_foundation_model: "anthropic.claude-3-haiku-20240307-v1:0"
```

### **Add More Specialists**
1. Create new Lambda function
2. Add new agent module call in `main.tf`
3. Update supervisor's collaborators list
4. Add new specialist to supervisor's coordination logic

### **Modify Agent Instructions**
Edit files in `agent_instructions/` directory to customize agent behavior.

## 🚨 Troubleshooting

### **Common Issues**
1. **Bedrock Model Access** - Ensure model access is enabled in AWS Console
2. **IAM Permissions** - Verify AWS credentials have required permissions
3. **S3 State Bucket** - Ensure bucket exists and is accessible
4. **Lambda Deployment** - Check Lambda function logs for errors

### **Monitoring**
- CloudWatch Logs for Lambda functions
- Bedrock agent invocation logs
- GitHub Actions workflow logs

## 🎉 Success Indicators

After successful deployment, you should see:
- ✅ 2 Bedrock agents created
- ✅ 2 Lambda functions deployed
- ✅ Agent aliases created
- ✅ Collaboration configured (Supervisor → Network Specialist)
- ✅ All IAM roles and policies in place
- ✅ Terraform outputs showing agent details

The system is now ready for production use with a supervisor agent that can intelligently coordinate with specialist agents to handle complex technical requests!