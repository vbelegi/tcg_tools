package main

import (
	"context"
	"log"
	"os"
	"os/signal"

	"github.com/vbelegi/tcg_tools/launcher/internal/app"
	"github.com/vbelegi/tcg_tools/launcher/internal/config"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatal(err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()

	application := app.New(cfg)
	if err := application.Run(ctx); err != nil {
		config.AppendLog(err.Error())
		log.Fatal(err)
	}
}
