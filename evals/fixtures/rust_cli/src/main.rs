use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct Order {
    id: u64,
    amount: f64,
}

fn main() {
    let order = Order { id: 1, amount: 42.0 };
    println!("{order:?}");
}
