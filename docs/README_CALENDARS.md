# Property Calendar Integration

This feature allows property owners to integrate their bookings from various platforms (Airbnb, VRBO, Booking.com, etc.) into the property management system using iCalendar feeds.

## Features

- Import bookings from multiple booking platforms
- Support for both entire property and individual room bookings
- Calendar sync status tracking
- Visual display of bookings with color-coding by platform
- Automated calendar synchronization

## How to Use

### Adding a Calendar

1. Navigate to a property's detail page
2. Click on "View Calendar" to see the calendar view
3. Click on "Manage Calendars" to see the list of calendars
4. Click "Add Calendar" to add a new calendar feed
5. Fill in the required information:
   - Name: A descriptive name for the calendar (e.g., "Airbnb Bookings")
   - iCal URL: The URL to the iCalendar feed from your booking platform
   - Service: Select the service this calendar is from (Airbnb, VRBO, Booking.com, Other)
   - Entire Property: Check if this calendar applies to the entire property, or uncheck to specify a room

### Obtaining iCal URLs

#### Airbnb
1. Log in to your Airbnb host account
2. Go to "Calendar" for your listing
3. Click on "Export Calendar" (usually under calendar settings)
4. Copy the iCal link provided

#### VRBO/HomeAway
1. Log in to your VRBO/HomeAway owner account
2. Go to "Calendar" for your listing
3. Look for "Calendar Sync" or "Export Calendar"
4. Copy the iCal link provided

#### Booking.com
1. Log in to your Booking.com extranet
2. Go to "Rates & Availability" → "Sync Calendar"
3. Click on "Export Calendar"
4. Copy the iCal link provided

### Viewing the Calendar

The calendar view provides a visual representation of all bookings:
- Bookings are color-coded by platform (Airbnb: red, VRBO: blue, Booking.com: navy)
- Click on any booking to see more details
- Use the calendar controls to navigate between months or switch to week view

### Managing Calendars

From the "Manage Calendars" page, you can:
- View the sync status of each calendar
- Manually trigger a sync for any calendar
- Edit calendar details
- Delete calendars

## Automated Calendar Sync

The system includes an automated calendar sync script that can be scheduled to run regularly to keep your bookings up to date.

### Setting Up Automated Sync

To set up automated sync, you can use a cron job (on Linux/Mac) or Task Scheduler (on Windows) to run the sync script periodically.

#### Example cron job (daily at 2 AM):

```
0 2 * * * cd /path/to/your/app && python -m app.tasks.sync_calendars >> /path/to/logs/cron.log 2>&1
```

#### Using the sync script manually:

```
python -m app.tasks.sync_calendars
```

## Troubleshooting

If you encounter issues with calendar synchronization:

1. Check that the iCal URL is correct and accessible
2. Verify that the URL belongs to the correct service
3. Check the sync status and error message in the "Manage Calendars" page
4. Try manually syncing the calendar
5. Check the log files at `calendar_sync.log` if running the sync script manually 