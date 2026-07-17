# Telegram Bot Deployment Guide

This guide provides instructions on how to run your Telegram bot locally using Termux and deploy it to Heroku for 24/7 operation.

## 1. Local Setup (Termux)

To run your bot on your Android phone using Termux, follow these steps:

1.  **Install Termux**: Download and install Termux from F-Droid or Google Play Store.

2.  **Update Termux**: Open Termux and run the following commands to update packages:
    ```bash
    pkg update && pkg upgrade
    ```

3.  **Install Python and Git**: Install Python and Git, which are necessary for running the bot and cloning the repository:
    ```bash
    pkg install python git
    ```

4.  **Clone your repository**: Clone your bot's GitHub repository to your Termux environment. Replace `your-username` and `your-repo-name` with your actual GitHub username and repository name:
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

5.  **Install Python dependencies**: Install the required Python libraries using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

6.  **Set Environment Variables**: Before running the bot, you need to set the environment variables for your API keys and other sensitive information. Replace the placeholder values with your actual credentials:
    ```bash
    export API_ID="YOUR_API_ID"
    export API_HASH="YOUR_API_HASH"
    export BOT_TOKEN="YOUR_BOT_TOKEN"
    export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    export ADMIN_ID="YOUR_ADMIN_ID"
    ```
    *Note: For `API_ID`, make sure it's an integer. For `GEMINI_API_KEY`, ensure it's on a single line.* 

7.  **Run the bot**: Start your bot:
    ```bash
    python bot.py
    ```
    The bot will now be running in your Termux session. It will stop if you close Termux or if the session is killed.

## 2. Heroku Deployment (for 24/7 Operation)

Heroku is a cloud platform that allows you to deploy and run your applications 24/7. Follow these steps to deploy your bot:

1.  **Sign up for Heroku**: If you don't have one, create a free Heroku account at [heroku.com](https://www.heroku.com/).

2.  **Install Heroku CLI**: Install the Heroku Command Line Interface (CLI) on your computer. Follow the instructions on the [Heroku Dev Center](https://devcenter.heroku.com/articles/heroku-cli).

3.  **Login to Heroku CLI**: Open your terminal/command prompt and log in to Heroku:
    ```bash
    heroku login
    ```

4.  **Create a Heroku App**: Navigate to your bot's project directory in your terminal and create a new Heroku app:
    ```bash
    heroku create your-bot-name
    ```
    Replace `your-bot-name` with a unique name for your Heroku app.

5.  **Set Buildpack**: Set the Python buildpack for your Heroku app:
    ```bash
    heroku buildpacks:set heroku/python
    ```

6.  **Configure Environment Variables**: Set your API keys and other sensitive information as environment variables (Config Vars) on Heroku. Replace the placeholder values with your actual credentials:
    ```bash
    heroku config:set API_ID="YOUR_API_ID"
    heroku config:set API_HASH="YOUR_API_HASH"
    heroku config:set BOT_TOKEN="YOUR_BOT_TOKEN"
    heroku config:set GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    heroku config:set ADMIN_ID="YOUR_ADMIN_ID"
    ```

7.  **Create a `Procfile`**: Create a file named `Procfile` (no extension) in the root of your project directory with the following content. This tells Heroku how to run your bot:
    ```
    worker: python bot.py
    ```

8.  **Deploy to Heroku**: Push your code to Heroku's Git remote:
    ```bash
    git add .
    git commit -m "Initial bot deployment"
    git push heroku main
    ```
    Heroku will now build and deploy your application. You can check the deployment logs using `heroku logs --tail`.

9.  **Scale your worker**: After deployment, ensure your worker process is running:
    ```bash
    heroku ps:scale worker=1
    ```
    Your bot should now be running 24/7 on Heroku.

## 3. GitHub Repository Setup

1.  **Initialize Git**: If you haven't already, initialize a Git repository in your project folder:
    ```bash
    git init
    ```

2.  **Create a new GitHub repository**: Go to [github.com](https://github.com/) and create a new **private** repository. Do NOT initialize it with a README, .gitignore, or license.

3.  **Add remote and push**: Add your GitHub repository as a remote and push your code:
    ```bash
    git remote add origin https://github.com/your-username/your-repo-name.git
    git branch -M main
    git push -u origin main
    ```
    Replace `your-username` and `your-repo-name` with your actual GitHub username and repository name.

4.  **Add GitHub Secrets**: In your GitHub repository, go to `Settings` > `Secrets and variables` > `Actions` > `New repository secret`. Add the following secrets with their corresponding values:
    *   `API_ID`
    *   `API_HASH`
    *   `BOT_TOKEN`
    *   `GEMINI_API_KEY`
    *   `ADMIN_ID`

    These secrets will be used by your GitHub Actions workflow.
