# Home Assistant Inky Impressions Dashboard
This project is a way to display a custom Home Assistant dashboard to a Pimproni
 Inky Impressions colour e-ink display.

# Setup
1. Create a long lived access token in Home Assistant (Profile -> Long-Lived Access Tokens)
2. Copy `.env.example` to `.env`
3. Edit `.env` to include your Home Assistant URL and the long lived access token
4. Run `make setup` to install dependencies and set up the environment
5. Run `make run` to start a mock display

# Deploying to the Inky Impressions
1. Perform the setup from above
2. Ensure your `.env` file includes all info about your Raspberry Pi
3. Run `make setup-deploy` to set up the Raspberry Pi dependencies
4. Run `make deploy` to deploy the code to your Raspberry Pi and start the service
5. The service will automatically start on boot and refresh the display according to the `DISPLAY_WAIT_TIME` in your `.env` file.

# Updating env variables after deployment
1. Tweak your `.env` file as needed
2. Run `make deploy-env` to update the `.env` file on the Raspberry Pi and restart the service
