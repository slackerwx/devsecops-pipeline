var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", () => Program.Greeting());
app.MapGet("/health", () => Results.Json(new { ok = true }));

app.Run();

public partial class Program
{
    public static string Greeting() => "fixture-dotnet";
}
