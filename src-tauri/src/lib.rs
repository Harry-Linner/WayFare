#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
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
      
      // Initialize backend services
      let app_handle = app.handle();
      
      // Start file system monitor
      std::thread::spawn(move || {
        file_monitor::start_file_monitor(app_handle.clone());
      });
      
      // Start agent scheduler
      let app_handle = app.handle();
      std::thread::spawn(move || {
        agent_scheduler::start_agent_scheduler(app_handle.clone());
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
