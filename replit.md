# Sistem Pemantauan Imunisasi Lombok Tengah

## Overview

This is a Flask-based web application for monitoring immunization programs in Central Lombok, Indonesia. The system integrates SMS gateway functionality with local Sasak cultural values to improve immunization coverage. It provides both web-based dashboard access for health workers and SMS-based interaction for parents and community members.

## System Architecture

The application follows a traditional Flask web architecture with the following components:

- **Backend**: Flask web framework with SQLAlchemy ORM
- **Database**: SQLite (development) with PostgreSQL support for production
- **Frontend**: HTML templates with Bootstrap for responsive UI
- **SMS Gateway**: Twilio integration for SMS communication
- **Task Scheduling**: APScheduler for automated reminder sending
- **Deployment**: Gunicorn WSGI server with autoscale deployment

## Key Components

### Database Models
- **Baby**: Stores baby registration data (ID, name, birth date, mother's name, village, parent phone)
- **Schedule**: Tracks immunization schedules and completion status
- **Village**: Contains village information and traditional coordinators
- **SMSLog**: Logs all SMS communications with error tracking
- **HealthWorker**: Stores health worker information for SMS authentication
- **User**: Authentication system with admin/operator roles and password management

### Core Services
- **SMS Service**: Handles incoming/outgoing SMS processing with automated responses
- **Scheduler**: Background job system for sending daily reminders and educational messages
- **Utility Functions**: Baby ID generation, immunization schedule calculation, cultural message handling

### Web Interface
- **Authentication**: Secure login system with session management
- **Dashboard**: Statistics overview with charts and recent activities (login required)
- **Baby Management**: Registration and data viewing interface (login required)
- **Schedule Management**: Immunization schedule tracking (login required)
- **SMS Logs**: Communication history and testing interface (login required)
- **Village Management**: Cultural coordinator and community data (login required)
- **Admin Panel**: User management interface (admin only)

## Data Flow

1. **Registration Flow**: Parents send SMS → System parses registration → Creates baby record → Generates immunization schedule → Sends confirmation SMS
2. **Reminder Flow**: Scheduler triggers daily → Queries upcoming schedules → Sends cultural-aware reminder SMS
3. **Reporting Flow**: Health workers report completion via SMS → System updates schedule status → Sends confirmation
4. **Monitoring Flow**: Web dashboard displays real-time statistics and completion rates

## External Dependencies

### Core Dependencies
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **APScheduler**: Background job scheduling
- **Twilio**: SMS gateway service
- **Gunicorn**: Production WSGI server

### Frontend Dependencies
- **Bootstrap**: UI framework with dark theme
- **Feather Icons**: Icon library
- **Chart.js**: Data visualization

## Deployment Strategy

The application is configured for Replit deployment with:
- **Development**: Flask dev server with auto-reload
- **Production**: Gunicorn with auto-scaling
- **Database**: SQLite for development, PostgreSQL for production
- **Environment**: Python 3.11 with Nix package management

The deployment uses environment variables for configuration:
- `DATABASE_URL`: Database connection string
- `SESSION_SECRET`: Flask session encryption key

## Changelog

- June 23, 2025. Initial setup
- June 23, 2025. Added complete authentication system with administrator login:
  - Implemented Flask-Login with User model and role-based access
  - Created admin/operator roles with different permissions
  - Added user management interface for administrators
  - Default admin account: username=admin, password=admin123
  - Protected all routes with login requirement
  - Integrated Twilio SMS with fallback to simulation mode
  - Fixed SQL compatibility issues with PostgreSQL
- June 23, 2025. Enhanced system with advanced analytics and cultural integration:
  - Built comprehensive analytics dashboard with dropout prediction
  - Implemented cultural integration module with Sasak language support
  - Added community engagement planning for villages
  - Enhanced SMS service with cultural messaging
  - Created intervention targeting based on performance data
  - Added village coordinator management system
- June 23, 2025. Completed system integration and deployment readiness:
  - Fixed circular import issues and database schema conflicts
  - Connected all code components and resolved application startup
  - Added comprehensive health monitoring and auto-recovery system
  - Created demo data generator for testing and demonstration
  - System now fully operational with authentication, analytics, and cultural features
  - Ready for production deployment with Twilio SMS integration

## User Preferences

Preferred communication style: Simple, everyday language.

## System Status

✅ **Application Status**: Fully operational and running on port 5000
✅ **Authentication**: Complete with admin/operator roles (admin/admin123, operator/operator123)  
✅ **Database**: PostgreSQL connected with sample data
✅ **SMS Service**: Integrated with Twilio (simulation mode if no credentials)
✅ **Analytics**: Advanced dashboard with dropout prediction and cultural insights
✅ **Cultural Integration**: Deep Sasak language support and community engagement
✅ **Health Monitoring**: Auto-recovery system and comprehensive error handling
✅ **Demo Data**: Sample babies, schedules, and SMS logs for testing

## Quick Start Guide

1. **Login**: Use admin/admin123 or operator/operator123
2. **Test SMS**: Use the SMS simulator in the system  
3. **View Analytics**: Access advanced analytics via Admin > Analytics
4. **Cultural Features**: Check Admin > Kearifan Lokal for cultural integration
5. **Add Twilio**: Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER for real SMS

The system is production-ready and can be deployed immediately.