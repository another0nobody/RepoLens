import { useEffect, useState } from "react";

import { fetchOrders } from "./api/client";
import TechCard from "./components/TechCard";

export default function App() {
  const [orders, setOrders] = useState<Array<{ id: number; status: string }>>([]);

  useEffect(() => {
    fetchOrders().then(setOrders).catch(() => setOrders([]));
  }, []);

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="text-3xl font-bold">Demo Shop</h1>
      <p className="mt-2 text-slate-500">一个用于演示技术栈分析的前端。</p>

      <section className="mt-8 grid gap-4">
        {orders.map((order) => (
          <TechCard key={order.id} title={`订单 #${order.id}`} badge={order.status} />
        ))}
      </section>
    </main>
  );
}
