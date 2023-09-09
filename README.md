# eas-slack-updates
Simple python script for managing Expo Application Service (EAS) build/submit webhooks. Generates QR codes using Cloudinary and sends a slack message.

![image](https://github.com/lumamontes/eas-slack-updates/assets/60052718/3cf36f27-0354-4079-8cc4-6178732af672)

### Set Up Slack Webhook
- [Obtain a Slack webhook URL for sending notifications](https://api.slack.com/messaging/webhooks)

### Set up Expo webhook

- Create a [expo webhook](https://docs.expo.dev/eas/webhooks/) for build/submit actions (on development, you can use [ngrok](https://ngrok.com/) to expose your local development server and create a expo webhook using the ngrok URL for testing)

### Run locally

1. Clone this repository to your local machine.

2. Create a .env file in the project directory and add your configuration details:
 
```
CLOUDINARY_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
SLACK_WEBHOOK_URL=your_slack_webhook_url
EXPO_WEBHOOK_SECRET_KEY=your_expo_webhook_secret_key
```

3. Install the required Python dependencies using the provided `requirements.txt` file:

   ```bash
   pip install -r requirements.txt
