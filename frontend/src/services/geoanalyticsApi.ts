import axios from "axios";

const API = "http://localhost:8001/metrics";

export const fetchDensity = (params: any) =>
  axios.get(`${API}/density`, { params }).then(res => res.data);

export const fetchWeightedDensity = (params: any) =>
  axios.get(`${API}/density_pondered`, { params }).then(res => res.data);

export const fetchAccessibility = (params: any) =>
  axios.get(`${API}/accessibility_score`, { params }).then(res => res.data);
