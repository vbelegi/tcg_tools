package main

import (
	"context"
	"os"
	"os/signal"
	"runtime"

	"github.com/vbelegi/tcg_tools/launcher/internal/app"
	"github.com/vbelegi/tcg_tools/launcher/internal/config"
	"github.com/vbelegi/tcg_tools/launcher/internal/instance"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		fail(err)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()

	application := app.New(cfg)
	if err := application.Run(ctx); err != nil {
		fail(err)
	}
}

func fail(err error) {
	config.AppendLog(err.Error())
	if runtime.GOOS == "windows" {
		instance.NotifyError("TCG Tools", err.Error())
	}
	os.Exit(1)
}
