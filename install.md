# Deploying bblp-tg.py in a Proxmox LXC Container

This guide provides step-by-step instructions to deploy and run the `bblp-tg.py` application within a Proxmox LXC container.

## 1. Create the LXC Container

1.  **Download a Template:** In your Proxmox web UI, navigate to your local storage -> CT Templates and download a suitable template. **Debian 12** or **Ubuntu 24.04** are recommended.
2.  **Create the Container:**
    *   Click the "Create CT" button in the Proxmox UI.
    *   **Hostname:** `bblp-tg`
    *   **Template:** Select the Debian or Ubuntu template you downloaded.
    *   **Disks:** Allocate at least 8 GB of disk space.
    *   **CPU:** Assign 1 or 2 cores.
    *   **Memory:** Assign at least 512 MB of RAM.
    *   **Network:** Configure a static IP address or use DHCP, depending on your network setup.
    *   **DNS:** Leave as is or configure as needed.
    *   Confirm and create the container.
3.  **Start the Container:** Once created, select the container and click "Start".

## 2. Prepare the System

1.  **Access the Console:** Open the container's console through the Proxmox UI.
2.  **Update System Packages:**
    ```bash
    apt update
    apt upgrade -y
    ```
3.  **Install Dependencies:**
    ```bash
    apt install -y python3 python3-pip git
    ```

## 3. Clone the Application

Clone the repository containing the `bblp-tg.py` script into the container. Replace `<your-repo-url>` with the actual URL to your git repository.

```bash
git clone <your-repo-url> /opt/bblp-tg
cd /opt/bblp-tg
```

### Alternative: Uploading Files with WinSCP

If you are not using a git repository, you can upload the files directly using WinSCP.

1.  **Create Application Directory:** In the LXC console, create the directory for the application.
    ```bash
    mkdir -p /opt/bblp-tg
    ```
2.  **Connect with WinSCP:**
    *   Open WinSCP and start a new session.
    *   **File protocol:** `SFTP`
    *   **Host name:** The IP address of your LXC container.
    *   **Port number:** `22`
    *   **User name:** `root`
    *   **Password:** Your root password.
    *   Click "Login".
3.  **Upload Files:**
    *   In the right-hand panel (remote server), navigate to `/opt/bblp-tg`.
    *   In the left-hand panel (your computer), navigate to your project directory.
    *   Select all the necessary application files and folders (`bblp-tg.py`, `requirements.txt`, `.env`, `cfg.json`, `static/`, `templates/`, etc.) and drag them to the remote directory.

## 4. Install Python Dependencies

Install the required Python libraries using the `requirements.txt` file.

```bash
pip3 install -r requirements.txt
```

## 5. Configure the Application

1.  **Environment Variables:**
    *   Copy the example `.env` file.
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file with your specific settings.
        ```bash
        nano .env
        ```
    *   Set the following values:
        *   `TB_TOKEN`: Your Telegram Bot token.
        *   `CHAT_ID`: The ID of the Telegram chat where notifications will be sent.
        *   `HTTP_PORT`: The port for the web interface (e.g., `5000`).

2.  **Printer Configuration:**
    *   Copy the example `cfg.json` file.
        ```bash
        cp cfg.json.example cfg.json
        ```
    *   Edit the `cfg.json` file to add your Bambu Lab printer details.
        ```bash
        nano cfg.json
        ```
    *   Update the `name`, `device_type`, `serial`, `host` (IP address), and `access_code` for each printer.

## 6. Create a systemd Service (Recommended)

Running the application as a `systemd` service ensures it starts automatically on boot and restarts if it fails.

1.  **Create the Service File:**
    ```bash
    nano /etc/systemd/system/bblp-tg.service
    ```
2.  **Add Service Configuration:** Paste the following content into the file.

    ```ini
    [Unit]
    Description=BBLP-TG Bambu Lab Telegram Bot
    After=network.target

    [Service]
    User=root
    WorkingDirectory=/opt/bblp-tg
    ExecStart=/usr/bin/python3 /opt/bblp-tg/bblp-tg.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

3.  **Enable and Start the Service:**
    *   Reload the `systemd` daemon to recognize the new service file.
        ```bash
        systemctl daemon-reload
        ```
    *   Enable the service to start on boot.
        ```bash
        systemctl enable bblp-tg.service
        ```
    *   Start the service immediately.
        ```bash
        systemctl start bblp-tg.service
        ```

## 7. Verify the Service

You can check the status of the service to ensure it is running correctly.

```bash
systemctl status bblp-tg.service
```

You should see an "active (running)" status. If there are issues, you can view the logs using:

```bash
journalctl -u bblp-tg.service -f
```

## 8. Access the Web Interface

You can now access the web interface by navigating to the IP address of your LXC container and the port you configured in the `.env` file (e.g., `http://<your-lxc-ip>:5000`).
