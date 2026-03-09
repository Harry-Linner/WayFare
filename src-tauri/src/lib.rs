#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  use tauri::Manager;
  
  tauri::Builder::default()
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      
      // Initialize database
      let app_dir = app.path().app_data_dir().unwrap_or_default();
      std::fs::create_dir_all(&app_dir).ok();
      let db_path = app_dir.join("wayfare.db");
      db::init_db(db_path.to_str().unwrap_or("wayfare.db")).ok();
      
      // Initialize notification system state
      let backend_url = std::env::var("BACKEND_URL")
        .unwrap_or_else(|_| "http://localhost:3001".to_string());
      let http_client = reqwest::Client::new();
      let notification_state = notifications::AppState {
        http_client,
        backend_url,
      };
      app.manage(notification_state);
      
      // Initialize backend services
      let app_handle = app.handle().clone();
      let app_handle_monitor = app_handle.clone();
      let app_handle_scheduler = app_handle.clone();
      
      // Start file system monitor
      std::thread::spawn(move || {
        file_monitor::start_file_monitor(app_handle_monitor);
      });
      
      // Start agent scheduler
      std::thread::spawn(move || {
        agent_scheduler::start_agent_scheduler(app_handle_scheduler);
      });
      
      Ok(())
    })
    .invoke_handler(tauri::generate_handler![
      commands::initialize_user_profile,
      commands::enrich_annotations,
      commands::fetch_supplementary_resources,
      commands::generate_learning_plan,
      commands::detect_stalled_interaction,
      commands::schedule_review_reminder,
      commands::analyze_learning_progress,
      commands::identify_misconception,
      commands::save_document,
      commands::get_document_annotations,
      commands::save_annotation,
      commands::record_learning_trace,
      commands::analyze_document_content,
      commands::search_resources,
      notifications::fetch_notifications,
      notifications::mark_notification_as_read,
      notifications::dismiss_notification,
      notifications::batch_dismiss_notifications,
      notifications::get_notification_preferences,
      notifications::update_notification_preferences,
      notifications::refresh_notification_stream,
      notifications::send_test_notification,
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}

pub mod file_monitor;
pub mod agent_scheduler;
pub mod memory_db;
pub mod commands;
pub mod utils;
pub mod db;
pub mod content_analyzer;
pub mod resource_fetcher;
pub mod notifications;
