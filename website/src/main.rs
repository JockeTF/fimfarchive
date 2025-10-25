use axum::Router;
use axum::response::Redirect;
use std::env::var;
use std::io::Result;
use tokio::net::TcpListener;
use tower_http::services::ServeDir;

const BIND: &str = "[::]:34407";
const CHUNK: usize = 16_777_216;
const PROFILE: &str = "https://www.fimfiction.net/user/116950/Fimfarchive";

fn releases() -> ServeDir {
    ServeDir::new("releases").with_buf_chunk_size(CHUNK)
}

#[tokio::main]
async fn main() -> Result<()> {
    let address = var("BIND").unwrap_or(BIND.into());
    let listener = TcpListener::bind(address).await?;

    let routes = Router::new()
        .nest_service("/releases", releases())
        .fallback(async || Redirect::to(PROFILE));

    axum::serve(listener, routes).await
}
