# Auto-Agents Setup Guide

## GitHub Repository Secrets

You need to configure the following secrets in your GitHub repository settings:

### Required Secrets

1. **AWS_ACCESS_KEY_ID**
   - Description: AWS Access Key ID for Terraform deployments
   - Value: Your AWS access key ID
   - Scope: Repository or Environment-specific

2. **AWS_SECRET_ACCESS_KEY**
   - Description: AWS Secret Access Key for Terraform deployments
   - Value: Your AWS secret access key
   - Scope: Repository or Environment-specific

3. **TF_STATE_BUCKET**
   - Description: S3 bucket name for storing Terraform state files
   - Value: Your S3 bucket name (e.g., `my-terraform-state-bucket`)
   - Scope: Repository

### AWS IAM Permissions Required

The AWS credentials need the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*",
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:PassRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:ListRolePolicies",
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:InvokeFunction",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    }
  ]
}
```

### Setting up GitHub Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret with the name and value as specified above

### Environment-Specific Secrets (Optional)

For better security, you can set up environment-specific secrets:

1. Go to **Settings** → **Environments**
2. Create environments: `production` and `test`
3. Add the same secrets to each environment with appropriate values

## AWS Prerequisites

### 1. Create S3 Bucket for Terraform State

```bash
aws s3 mb s3://your-terraform-state-bucket --region us-east-1
aws s3api put-bucket-versioning \
  --bucket your-terraform-state-bucket \
  --versioning-configuration Status=Enabled
```

### 2. Enable Bedrock Model Access

Ensure you have access to the required Bedrock models:

```bash
# List available models
aws bedrock list-foundation-models --region us-east-1

# Request model access if needed (via AWS Console)
# Go to AWS Bedrock Console → Model access → Request access
```

### 3. Create IAM User for GitHub Actions

```bash
# Create IAM user
aws iam create-user --user-name github-actions-bedrock

# Attach policy (create the policy first using the JSON above)
aws iam attach-user-policy \
  --user-name github-actions-bedrock \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT:policy/BedrockAgentsDeploymentPolicy

# Create access keys
aws iam create-access-key --user-name github-actions-bedrock
```

## Deployment Workflow

### Automatic Deployment (Main Branch)
- Push to `main` branch automatically deploys to production
- Creates stack: `auto-agents-prod`

### Feature Branch Testing
- Push to `feature/*` or `hotfix/*` branches
- Include `tf deploy` in commit message to trigger deployment
- Creates test stack: `auto-agents-test-{branch-name}`

### Manual Cleanup
- Test stacks older than 7 days are automatically identified
- Manual cleanup can be triggered via GitHub Actions

## Local Development

### Prerequisites
- Terraform >= 1.6.0
- AWS CLI configured
- Access to Bedrock models

### Setup
```bash
# Clone repository
git clone <your-repo-url>
cd bedrock-agents

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="foundation_model=anthropic.claude-3-5-sonnet-20241022-v2:0"

# Apply (for testing)
terraform apply -var="foundation_model=anthropic.claude-3-5-sonnet-20241022-v2:0"
```

## Troubleshooting

### Common Issues

1. **Bedrock Model Access Denied**
   - Solution: Request model access in AWS Bedrock Console

2. **S3 State Bucket Not Found**
   - Solution: Create the S3 bucket or update TF_STATE_BUCKET secret

3. **IAM Permission Denied**
   - Solution: Verify IAM permissions match the policy above

4. **Lambda Function Creation Failed**
   - Solution: Check Lambda service limits and IAM permissions

### Getting Help

- Check GitHub Actions logs for detailed error messages
- Verify AWS credentials and permissions
- Ensure all required secrets are configured
- Check AWS service limits and quotas