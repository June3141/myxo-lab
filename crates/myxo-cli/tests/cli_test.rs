use assert_cmd::Command;
use predicates::prelude::*;

fn cmd() -> Command {
    Command::cargo_bin("mxl").unwrap()
}

#[test]
fn help_succeeds() {
    cmd().arg("--help").assert().success();
}

#[test]
fn init_is_recognized() {
    cmd().arg("init").assert().success();
}

#[test]
fn sync_is_recognized() {
    cmd().arg("sync").assert().success();
}

#[test]
fn verify_is_recognized() {
    cmd().arg("verify").assert().success();
}

#[test]
fn verify_fix_flag_is_recognized() {
    cmd().args(["verify", "--fix"]).assert().success();
}

#[test]
fn unknown_subcommand_fails() {
    cmd()
        .arg("nonexistent")
        .assert()
        .failure()
        .stderr(predicate::str::contains("unrecognized subcommand"));
}
