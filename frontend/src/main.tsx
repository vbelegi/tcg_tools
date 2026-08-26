import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAdmin, RequireAuth } from "./components/RequireAuth";
import { AlterarSenhaPage } from "./pages/AlterarSenhaPage";
import { ClaimInvitePage } from "./pages/ClaimInvitePage";
import { Home } from "./pages/Home";
import { LoginPage } from "./pages/LoginPage";
import { PlayerProfilePage } from "./pages/PlayerProfilePage";
import { PremiacaoPage } from "./pages/premiacao/PremiacaoPage";
import { RankingPage } from "./pages/RankingPage";
import { SorteadorPage } from "./pages/sorteador/SorteadorPage";
import { TorneioDetailPage } from "./pages/torneios/TorneioDetailPage";
import { TorneioExternoPage } from "./pages/torneios/TorneioExternoPage";
import { TorneioNovoPage } from "./pages/torneios/TorneioNovoPage";
import { TorneioResultadoPage } from "./pages/torneios/TorneioResultadoPage";
import { TorneioRodadaPage } from "./pages/torneios/TorneioRodadaPage";
import { TorneiosListPage } from "./pages/torneios/TorneiosListPage";
import { UsuariosPage } from "./pages/UsuariosPage";
import "./index.css";

const queryClient = new QueryClient();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/convite/:token" element={<ClaimInvitePage />} />
          <Route element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="ranking" element={<RankingPage />} />
            <Route path="jogadores/:id" element={<PlayerProfilePage />} />
            <Route path="torneios" element={<TorneiosListPage />} />
            <Route path="torneios/:id" element={<TorneioDetailPage />} />
            <Route path="torneios/:id/resultado" element={<TorneioResultadoPage />} />
          </Route>
          <Route element={<RequireAuth />}>
            <Route element={<Layout />}>
              <Route path="premiacao" element={<PremiacaoPage />} />
              <Route path="sorteador" element={<SorteadorPage />} />
              <Route path="torneios/novo" element={<TorneioNovoPage />} />
              <Route path="torneios/externo" element={<TorneioExternoPage />} />
              <Route path="torneios/:id/rodadas/:n" element={<TorneioRodadaPage />} />
              <Route path="conta/senha" element={<AlterarSenhaPage />} />
            </Route>
          </Route>
          <Route element={<RequireAdmin />}>
            <Route element={<Layout />}>
              <Route path="usuarios" element={<UsuariosPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
