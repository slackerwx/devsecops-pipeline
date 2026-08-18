package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

func handler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path == "/health" {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, `{"ok":true}`)
		return
	}
	w.Header().Set("Content-Type", "text/plain")
	fmt.Fprintln(w, "fixture-go")
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	http.HandleFunc("/", handler)
	log.Printf("listening on %s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
