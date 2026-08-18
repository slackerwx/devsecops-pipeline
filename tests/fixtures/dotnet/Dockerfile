FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY src/Fixture.Api/Fixture.Api.csproj src/Fixture.Api/packages.lock.json src/Fixture.Api/
RUN dotnet restore src/Fixture.Api/Fixture.Api.csproj --locked-mode
COPY src ./src
RUN dotnet publish src/Fixture.Api/Fixture.Api.csproj -c Release -o /out --no-restore

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /out .
USER 1654
EXPOSE 8080
ENTRYPOINT ["dotnet", "Fixture.Api.dll"]
