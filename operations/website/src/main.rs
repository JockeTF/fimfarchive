use axum::Router;
use axum::response::Redirect;
use std::env::var;
use std::io::Result;
use tokio::net::TcpListener;
use tower_http::services::ServeDir;

const BIND: &str = "[::]:34407";
const PROFILE: &str = "https://www.fimfiction.net/user/116950/Fimfarchive";

#[tokio::main]
async fn main() -> Result<()> {
    let address = var("BIND").unwrap_or(BIND.into());
    let listener = TcpListener::bind(address).await?;

    let routes = Router::new()
        .nest_service("/releases", ServeDir::new("releases"))
        .fallback(async || Redirect::to(PROFILE));

    axum::serve(listener, routes).await
}
