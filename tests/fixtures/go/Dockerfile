FROM golang:1.26.6-bookworm AS build
WORKDIR /src
COPY go.mod ./
COPY *.go ./
RUN CGO_ENABLED=0 go build -trimpath -o /app .

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /app /app
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/app"]
