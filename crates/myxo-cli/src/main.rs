use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "mxl", about = "Myxo Lab CLI")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Initialize a new myxo project
    Init,
    /// Sync infrastructure state
    Sync {
        /// Target environment to sync
        #[arg(long)]
        target: Option<String>,
    },
    /// Verify infrastructure configuration
    Verify {
        /// Automatically fix issues
        #[arg(long)]
        fix: bool,
    },
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Command::Init => myxo_core::init(),
        Command::Sync { .. } => myxo_core::sync(),
        Command::Verify { .. } => myxo_core::verify(),
    }
}
