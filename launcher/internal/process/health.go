package process

import (
	"encoding/json"
	"io"
	"net/http"
)

const healthAppID = "tcg_tools"

type healthPayload struct {
	Status string `json:"status"`
	App    string `json:"app"`
}

func healthResponseOK(body io.Reader) bool {
	var payload healthPayload
	if err := json.NewDecoder(body).Decode(&payload); err != nil {
		return false
	}
	return payload.Status == "ok" && payload.App == healthAppID
}

func fetchHealthOK(client *http.Client, healthURL string) bool {
	resp, err := client.Get(healthURL)
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return false
	}
	return healthResponseOK(resp.Body)
}
