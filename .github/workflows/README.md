# GitHub Actions CI/CD Setup

This workflow automatically deploys your application to Vultr on each push to `main` or `master`.

## Prerequisites

1. **Vultr VM Instance** - You need a running Vultr VM instance
2. **SSH Access** - SSH keys set up for the VM
3. **GitHub Secrets** - Configure the following secrets in your GitHub repository

## Setup Instructions

### 1. Create a Vultr VM Instance

If you don't have one yet:
1. Go to https://my.vultr.com
2. Create a new Compute instance (Ubuntu 22.04 recommended)
3. Note the IP address
4. Set up SSH access (either password or SSH key)

### 2. Initial VM Setup (One-time)

SSH into your VM and run the initial setup:

```bash
ssh root@YOUR_VULTR_IP  # or ubuntu@YOUR_VULTR_IP

# Install Docker
bash <(curl -s https://raw.githubusercontent.com/Doomsy1/DeltaHacks12/main/scripts/vultr_setup.sh)

# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd DeltaHacks12  # or your repo name

# Create .env file (you'll need to do this manually the first time)
cp .env.example .env  # if you have one, or create it manually
nano .env  # Add your MongoDB URI and other credentials

# Do initial deployment to make sure everything works
docker compose -f docker-compose.prod.yml up -d --build
```

### 3. Set Up SSH Key for GitHub Actions

Generate an SSH key pair (if you don't have one specifically for this):

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-vultr" -f ~/.ssh/github_actions_vultr
```

**Add the public key to your Vultr VM:**

```bash
# Copy public key to VM
ssh-copy-id -i ~/.ssh/github_actions_vultr.pub root@YOUR_VULTR_IP

# Or manually on the VM:
# 1. SSH into VM
# 2. Run: mkdir -p ~/.ssh && chmod 700 ~/.ssh
# 3. Add the public key content to ~/.ssh/authorized_keys
# 4. chmod 600 ~/.ssh/authorized_keys
```

**Keep the private key safe** - you'll add it to GitHub secrets.

### 4. Configure GitHub Secrets

Go to your GitHub repository:
1. Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add the following secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `SSH_PRIVATE_KEY` | The private SSH key (entire content including `-----BEGIN` and `-----END`) | Content of `~/.ssh/github_actions_vultr` |
| `VULTR_HOST` | Your Vultr VM IP address | `192.0.2.1` |
| `VULTR_USER` | SSH user (usually `root` or `ubuntu`) | `root` |
| `VULTR_PROJECT_DIR` | Project directory name (optional, defaults to `DeltaHacks12`) | `DeltaHacks12` |

**To get your private key content:**
```bash
cat ~/.ssh/github_actions_vultr
# Copy the entire output including -----BEGIN OPENSSH PRIVATE KEY----- and -----END OPENSSH PRIVATE KEY-----
```

### 5. Verify the Workflow

1. Push a commit to `main` or `master` branch
2. Go to your GitHub repository → Actions tab
3. Watch the workflow run
4. Check the logs if anything fails

## How It Works

1. **Trigger**: Workflow runs on push to `main`/`master` or manual trigger
2. **Checkout**: GitHub Actions checks out your code
3. **SSH Setup**: Sets up SSH keys to connect to your Vultr VM
4. **Deploy**: 
   - Connects to VM via SSH
   - Navigates to project directory
   - Pulls latest code (`git reset --hard`)
   - Stops existing services
   - Builds and starts new services with `docker compose`
   - Checks service status
   - Tests health endpoint

## Troubleshooting

### Workflow fails with "Permission denied (publickey)"
- Verify `SSH_PRIVATE_KEY` secret contains the full private key (including headers)
- Check that the public key is in the VM's `~/.ssh/authorized_keys`
- Verify `VULTR_USER` matches the user on the VM
- Test SSH manually: `ssh -i ~/.ssh/github_actions_vultr root@YOUR_VULTR_IP`

### Workflow fails with "cd: no such file or directory"
- Check `VULTR_PROJECT_DIR` secret matches your actual directory name
- Verify the repo was cloned on the VM
- The workflow tries common locations: `~/DeltaHacks12`, `/root/DeltaHacks12`, `/home/USER/DeltaHacks12`

### Services fail to start
- Check `.env` file exists on the VM and has correct values
- Verify Docker is running: `ssh root@IP 'systemctl status docker'`
- Check logs: `ssh root@IP 'cd DeltaHacks12 && docker compose -f docker-compose.prod.yml logs'`

### Health check fails
- Services may still be starting (workflow waits 2 seconds)
- Check logs on VM: `docker compose -f docker-compose.prod.yml logs backend`

## Manual Deployment

You can also manually trigger the workflow:
1. Go to Actions tab
2. Select "Deploy to Vultr" workflow
3. Click "Run workflow"
4. Select branch and click "Run workflow"

## Security Notes

- **Never commit `.env` files** - they should only exist on the VM
- Use a dedicated SSH key for GitHub Actions (don't reuse your personal key)
- Consider using a non-root user for deployment (requires additional setup)
- Regularly rotate SSH keys
