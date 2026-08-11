# Cloud Deployment Options for Pulse Vector

To run the Pulse Vector daily automation pipeline 24/7 without maintaining a local machine, you can deploy it to a Cloud Virtual Machine (VM) or a Serverless Scheduler. Below is a detailed comparison of the best hosting options based on **minimizing cost** and **compatibility** with our application's resource needs.

---

## 🛠️ Application Resource Needs
1. **CPU & Memory**: Moderate CPU/RAM is required for **video compilation** (FFmpeg encoding) and **image generation** (Pillow). 1 GB RAM is the bare minimum; 2 GB or more is highly recommended to avoid Out-Of-Memory (OOM) crashes during video muxing.
2. **Disk Storage**: Today's pipeline generated about **10-15 MB** of files (images, audio, video). Over a year, this accumulates to **4-6 GB** of data. A 20+ GB SSD is ideal.
3. **External Integrations**: Requires outbound internet access for Google Search, Gemini API, and YouTube video uploads.
4. **Backup System**: In the cloud, a local path like `E:\PulseVectorBackups` will not work. We must transition this step to cloud storage (e.g. Google Drive API, AWS S3, or Rclone).

---

## 📊 Comparison of Cloud Deployment Options

| Provider / Option | Specs (vCPU / RAM / SSD) | Cost / Month (USD) | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GitHub Actions** (Serverless Cron) | 2 vCPU / 7 GB RAM / 14 GB | **$0.00** (Free) | - 100% Free (2,000 mins/mo free)<br>- High specs (7GB RAM)<br>- Perfect for 2-min daily runs | - No persistent storage (must push to Git or Google Drive)<br>- Not a 24/7 VM | **Highly Recommended** (If you don't strictly need a 24/7 active terminal). |
| **Oracle Cloud (OCI)** (Always Free ARM) | Up to 4 vCPU ARM / 24 GB RAM / 200 GB | **$0.00** (Free) | - Massive free resources<br>- 24/7 VM<br>- Generous SSD | - High demand makes ARM instances hard to provision in some regions. | **Recommended** (Best free 24/7 VM option if available). |
| **Hetzner Cloud** (CAX11 ARM / Shared) | 2 vCPU ARM / 4 GB RAM / 40 GB | **~$3.60 / mo** (€3.29) | - Extremely cheap<br>- Plenty of RAM/SSD for encoding<br>- Highly reliable | - Not free<br>- ARM architecture | **Highly Recommended** (Best paid VPS for performance/cost). |
| **GCP (Compute Engine)** (e2-micro Free Tier) | 2 vCPU (Shared) / 1 GB RAM / 30 GB | **$0.00** (Free) | - 24/7 VM<br>- Google Cloud ecosystem | - 1 GB RAM is tight and might cause FFmpeg crashes during rendering. | **Alternative** (Good if OCI is unavailable). |
| **AWS Lightsail** (Starter Tier) | 1 vCPU / 512 MB RAM / 20 GB | **$3.50 / mo** (First 3 months free) | - Easy setup<br>- AWS reliability | - 512 MB RAM is too low for video encoding. | **Not Recommended** (Too low RAM for FFmpeg). |
| **AWS Lightsail** (Medium Tier) | 1 vCPU / 1 GB RAM / 40 GB | **$5.00 / mo** | - Adequate SSD | - Prone to OOM on 1GB RAM if background jobs run. | **Alternative** |
| **DigitalOcean / Linode** (Basic Droplet) | 1 vCPU / 1 GB RAM / 25 GB | **$4.00–$6.00 / mo** | - Easy to manage<br>- Excellent docs | - Standard pricing, not the absolute cheapest. | **Alternative** |

---

## 💡 Recommended Architecture

### Option A: GitHub Actions (Free & Zero Infrastructure)
Since the script takes under 2 minutes to run once a day, you don't actually need a server running 24/7. You can use GitHub Actions to trigger a cron job every morning:
- **How it works**: A GitHub workflow file installs Python/FFmpeg, pulls the latest changes, runs the script, uploads the compiled video to YouTube, commits the generated archive files back to GitHub, and exits.
- **Cost**: **$0.00/month** (runs take ~2 minutes daily, totaling ~60 minutes/month out of your 2,000 free minutes).

### Option B: Hetzner Cloud (Paid VM - Best Performance/Price)
If you want a 24/7 active Linux machine to log in, run test runs, and monitor logs manually:
- **Instance**: Hetzner **CAX11** (ARM-based) or **CX21** (Intel/AMD).
- **Cost**: **~$3.60/month** (€3.29).
- **Setup**: Install Python 3, Git, and FFmpeg via `apt`, configure a Linux `cron` job to run the script at 8:00 AM daily, and save outputs locally or sync them to Google Drive.

---

## ⚙️ Key Code Adjustions Needed for Cloud Deployment

Regardless of the cloud option you choose, we will need to adjust the following:
1. **FFmpeg Path**: Ensure FFmpeg is installed via the system package manager (e.g. `sudo apt install ffmpeg` on Ubuntu/Linux) and that `imageio_ffmpeg` resolves it correctly on Linux.
2. **Google OAuth (YouTube)**: In a headless cloud environment, a browser window cannot open for OAuth login. We will need to pre-generate the `token.json` locally and upload it along with the project files to the VM.
3. **Backup Destination**: Replace the local directory backup logic in `run_backup_operations()` with a cloud-native backup tool (like uploading to a Google Drive folder via the Google API, or setting up a free AWS S3 bucket/Cloudflare R2 bucket with Rclone).
