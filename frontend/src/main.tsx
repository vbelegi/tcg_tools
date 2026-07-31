import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Home } from "./pages/Home";
import { PremiacaoPage } from "./pages/premiacao/PremiacaoPage";
import { SorteadorPage } from "./pages/sorteador/SorteadorPage";
import { TorneioDetailPage } from "./pages/torneios/TorneioDetailPage";
import { TorneioNovoPage } from "./pages/torneios/TorneioNovoPage";
import { TorneioResultadoPage } from "./pages/torneios/TorneioResultadoPage";
import { TorneioRodadaPage } from "./pages/torneios/TorneioRodadaPage";
import { TorneiosListPage } from "./pages/torneios/TorneiosListPage";
import "./index.css";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="premiacao" element={<PremiacaoPage />} />
            <Route path="sorteador" element={<SorteadorPage />} />
            <Route path="torneios" element={<TorneiosListPage />} />
            <Route path="torneios/novo" element={<TorneioNovoPage />} />
            <Route path="torneios/:id" element={<TorneioDetailPage />} />
            <Route path="torneios/:id/rodadas/:n" element={<TorneioRodadaPage />} />
            <Route path="torneios/:id/resultado" element={<TorneioResultadoPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
