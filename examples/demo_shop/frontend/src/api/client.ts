import axios from "axios";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? "http://localhost:8000",
  timeout: 5000
});

export async function fetchOrders(): Promise<Array<{ id: number; status: string }>> {
  const response = await http.get("/api/orders");
  return response.data;
}
