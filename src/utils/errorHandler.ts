import type { App } from 'vue'

export function setupErrorHandler(app: App) {
  // Global error handler for Vue component errors
  app.config.errorHandler = (err, instance, info) => {
    console.error('Vue Global Error Handler:', {
      error: err,
      instance,
      info
    })
    
    // You could send this to an error logging service here
    // Example: Sentry.captureException(err)
    
    // Log to standard output/console for development
    alert(`An unexpected error occurred in the component: ${err}`)
  }

  // Global handler for unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled Promise Rejection:', {
      reason: event.reason,
      promise: event.promise
    })
    
    // Prevent default browser logging if handled
    // event.preventDefault()
  })

  // Global handler for runtime errors
  window.addEventListener('error', (event) => {
    console.error('Global Runtime Error:', {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      error: event.error
    })
  })
}
