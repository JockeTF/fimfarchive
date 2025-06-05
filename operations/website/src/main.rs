use axum::Router;
use axum::extract::Request;
use axum::middleware;
use axum::middleware::Next;
use axum::response::IntoResponse;
use axum::response::Redirect;
use axum::response::Response;
use axum_extra::extract::Host;
use std::env::var;
use std::io::Result;
use tokio::net::TcpListener;
use tower_http::services::ServeDir;

const BIND: &str = "[::]:34407";
const HOST: &str = "www.fimfarchive.net";
const PROFILE: &str = "https://www.fimfiction.net/user/116950/Fimfarchive";

async fn canonicalize(Host(host): Host, req: Request, next: Next) -> Response {
    let canon = var("HOST").unwrap_or(HOST.into());

    if host == canon {
        next.run(req).await
    } else {
        let path = req.uri().path_and_query().unwrap();
        let url = format!("https://{canon}{path}");
        Redirect::to(&url).into_response()
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    let address = var("BIND").unwrap_or(BIND.into());
    let listener = TcpListener::bind(address).await?;

    let routes = Router::new()
        .nest_service("/releases", ServeDir::new("releases"))
        .fallback(async || Redirect::to(PROFILE))
        .layer(middleware::from_fn(canonicalize));

    axum::serve(listener, routes).await
}
